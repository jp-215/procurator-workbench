"""Order lifecycle — see SPEC.md AC-05..AC-15."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ordersvc import auth
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

    @property
    def total(self) -> float:
        total = 0.0
        for item in self.items:
            total += item["qty"] * item["unit_price"]
        return round(total, 2)


_store = MemoryStore()
_idempotency: dict[str, str] = {}

_VALID_TRANSITIONS = {
    ("pending", "paid"),
    ("paid", "shipped"),
    ("pending", "cancelled"),
}


def _validate_items(items: list[dict[str, Any]]) -> None:
    if not items:
        raise ValidationError("items must be a non-empty list")
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("each item must be a dict")
        if "sku" not in item or "qty" not in item or "unit_price" not in item:
            raise ValidationError("each item must have sku, qty, unit_price")
        sku = item["sku"]
        qty = item["qty"]
        unit_price = item["unit_price"]
        if not isinstance(sku, str):
            raise ValidationError("sku must be a string")
        if not isinstance(qty, int) or isinstance(qty, bool):
            raise ValidationError("qty must be an int")
        if not isinstance(unit_price, (int, float)) or isinstance(unit_price, bool):
            raise ValidationError("unit_price must be a number")


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key is not None and idempotency_key in _idempotency:
        existing_id = _idempotency[idempotency_key]
        return _store.get(existing_id)

    _validate_items(items)

    order_id = uuid.uuid4().hex
    order = Order(
        id=order_id,
        user_id=user_id,
        items=items,
        status="pending",
        created_at=time.time(),
    )
    _store.put(order_id, order)

    if idempotency_key is not None:
        _idempotency[idempotency_key] = order_id

    return order


def get_order(order_id: str) -> Order:
    try:
        return _store.get(order_id)
    except KeyError:
        raise OrderNotFound(f"no order with id {order_id!r}")


def _transition(order: Order, new_status: str) -> Order:
    if (order.status, new_status) not in _VALID_TRANSITIONS:
        raise InvalidTransition(
            f"cannot transition order from {order.status!r} to {new_status!r}"
        )
    order.status = new_status
    _store.put(order.id, order)
    return order


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)
    return _transition(order, "cancelled")


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = auth.verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden("token does not belong to the order owner")
    return _transition(order, "paid")


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)
    return _transition(order, "shipped")


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    result = []
    for order in _store.values():
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        result.append(order)
    return result


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    global _store
    _store = MemoryStore()
    _idempotency.clear()