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
        total = sum(item["qty"] * item["unit_price"] for item in self.items)
        return round(total, 2)


_STORE = MemoryStore()
_IDEMPOTENCY: dict[str, str] = {}

# Valid state transitions: (current_status) -> (new_status)
_TRANSITIONS = {
    "pay": ("pending", "paid"),
    "ship": ("paid", "shipped"),
    "cancel": ("pending", "cancelled"),
}


def _validate_items(items: list[dict[str, Any]]) -> None:
    if not items:
        raise ValidationError("items must be a non-empty list")
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("each item must be a dict")
        if "sku" not in item or not isinstance(item["sku"], str) or not item["sku"]:
            raise ValidationError("item.sku must be a non-empty string")
        if "qty" not in item or not isinstance(item["qty"], int) or isinstance(item["qty"], bool):
            raise ValidationError("item.qty must be an int")
        if item["qty"] <= 0:
            raise ValidationError("item.qty must be positive")
        if "unit_price" not in item or not isinstance(item["unit_price"], (int, float)) or isinstance(
            item["unit_price"], bool
        ):
            raise ValidationError("item.unit_price must be a number")
        if item["unit_price"] < 0:
            raise ValidationError("item.unit_price must be non-negative")


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key is not None and idempotency_key in _IDEMPOTENCY:
        existing_id = _IDEMPOTENCY[idempotency_key]
        return _STORE.get(existing_id)

    _validate_items(items)

    order_id = str(uuid.uuid4())
    order = Order(
        id=order_id,
        user_id=user_id,
        items=items,
        status="pending",
        created_at=time.time(),
    )
    _STORE.put(order_id, order)

    if idempotency_key is not None:
        _IDEMPOTENCY[idempotency_key] = order_id

    return order


def get_order(order_id: str) -> Order:
    try:
        return _STORE.get(order_id)
    except KeyError:
        raise OrderNotFound(f"no order with id {order_id!r}")


def _transition(order_id: str, action: str) -> Order:
    order = get_order(order_id)
    required_from, to_status = _TRANSITIONS[action]
    if order.status != required_from:
        raise InvalidTransition(
            f"cannot {action} order in status {order.status!r}"
        )
    order.status = to_status
    _STORE.put(order_id, order)
    return order


def cancel_order(order_id: str) -> Order:
    return _transition(order_id, "cancel")


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden("token user is not the order owner")
    return _transition(order_id, "pay")


def ship_order(order_id: str) -> Order:
    return _transition(order_id, "ship")


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    result = []
    for order in _STORE.values():
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        result.append(order)
    return result


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    for key in list(_STORE.keys()):
        _STORE.delete(key)
    _IDEMPOTENCY.clear()