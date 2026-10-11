"""Order lifecycle — see SPEC.md AC-05..AC-15."""
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
from ordersvc.store import default_store

_ORDER_PREFIX = "order:"
_IDEMPOTENCY_PREFIX = "idemp:"


@dataclass
class Order:
    id: str = ""
    user_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: float = 0.0

    @property
    def total(self) -> float:
        total = 0.0
        for item in self.items:
            qty = item["qty"]
            unit_price = item["unit_price"]
            total += qty * unit_price
        return round(total, 2)


def _order_key(order_id: str) -> str:
    return f"{_ORDER_PREFIX}{order_id}"


def _idempotency_key(key: str) -> str:
    return f"{_IDEMPOTENCY_PREFIX}{key}"


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if not items:
        raise ValidationError("items must not be empty")

    if idempotency_key is not None:
        try:
            existing_id = default_store.get(_idempotency_key(idempotency_key))
        except KeyError:
            pass
        else:
            return get_order(existing_id)

    order = Order(
        id=str(uuid.uuid4()),
        user_id=user_id,
        items=items,
        status="pending",
        created_at=time.time(),
    )
    default_store.put(_order_key(order.id), order)

    if idempotency_key is not None:
        default_store.put(_idempotency_key(idempotency_key), order.id)

    return order


def get_order(order_id: str) -> Order:
    try:
        return default_store.get(_order_key(order_id))
    except KeyError:
        raise OrderNotFound(f"unknown order: {order_id!r}")


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "pending":
        raise InvalidTransition(
            f"cannot cancel order in status {order.status!r}"
        )
    order.status = "cancelled"
    default_store.put(_order_key(order.id), order)
    return order


def pay_order(order_id: str, token: str) -> Order:
    owner_id = verify_token(token)
    order = get_order(order_id)
    if order.user_id != owner_id:
        raise Forbidden("token does not belong to order owner")
    if order.status != "pending":
        raise InvalidTransition(
            f"cannot pay order in status {order.status!r}"
        )
    order.status = "paid"
    default_store.put(_order_key(order.id), order)
    return order


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "paid":
        raise InvalidTransition(
            f"cannot ship order in status {order.status!r}"
        )
    order.status = "shipped"
    default_store.put(_order_key(order.id), order)
    return order


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    results = []
    for key, value in default_store.items():
        if not key.startswith(_ORDER_PREFIX):
            continue
        order = value
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        results.append(order)
    return results


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    default_store.clear()