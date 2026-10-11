"""Order lifecycle — see SPEC.md AC-05..AC-15, AC-26..AC-32."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ordersvc.auth import verify_token
from ordersvc.errors import (
    Forbidden,
    InvalidTransition,
    OrderNotFound,
    ValidationError,
)
from ordersvc.store import MemoryStore


@dataclass
class Order:
    id: str = ""
    user_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: float = 0.0
    idempotency_key: str | None = None
    refund_amount: float = 0.0

    @property
    def total(self) -> float:
        return round(sum(item["qty"] * item["unit_price"] for item in self.items), 2)


# Module-level store for orders, plus an idempotency-key -> order-id index.
_store = MemoryStore()
_idempotency_index: dict[str, str] = {}


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if not items:
        raise ValidationError("items must not be empty")

    if idempotency_key is not None and idempotency_key in _idempotency_index:
        existing_id = _idempotency_index[idempotency_key]
        return _store.get(existing_id)

    order_id = uuid.uuid4().hex
    order = Order(
        id=order_id,
        user_id=user_id,
        items=items,
        status="pending",
        created_at=time.time(),
        idempotency_key=idempotency_key,
        refund_amount=0.0,
    )
    _store.put(order_id, order)
    if idempotency_key is not None:
        _idempotency_index[idempotency_key] = order_id
    return order


def get_order(order_id: str) -> Order:
    try:
        return _store.get(order_id)
    except KeyError:
        raise OrderNotFound(f"no such order: {order_id!r}")


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "pending":
        raise InvalidTransition(
            f"cannot cancel order in status {order.status!r}"
        )
    order.status = "cancelled"
    _store.put(order_id, order)
    return order


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden("token user is not the order owner")
    if order.status != "pending":
        raise InvalidTransition(
            f"cannot pay order in status {order.status!r}"
        )
    order.status = "paid"
    _store.put(order_id, order)
    return order


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "paid":
        raise InvalidTransition(
            f"cannot ship order in status {order.status!r}"
        )
    order.status = "shipped"
    _store.put(order_id, order)
    return order


def refund_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden("token user is not the order owner")
    if order.status != "shipped":
        raise InvalidTransition(
            f"cannot refund order in status {order.status!r}"
        )
    order.status = "refunded"
    order.refund_amount = round(order.total, 2)
    _store.put(order_id, order)
    return order


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    result: list[Order] = []
    for key in list(_store._data.keys()):
        order = _store.get(key)
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        result.append(order)
    return result


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    global _store, _idempotency_index
    _store = MemoryStore()
    _idempotency_index = {}