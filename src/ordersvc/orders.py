"""Order lifecycle — see SPEC.md AC-05..AC-15."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ordersvc.auth import verify_token
from ordersvc.errors import (
    ValidationError,
    OrderNotFound,
    InvalidTransition,
    Forbidden,
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
        return round(
            sum(item["qty"] * item["unit_price"] for item in self.items), 2
        )


# Module-level storage
_STORE = MemoryStore()
_IDEMPOTENCY: dict[str, str] = {}


def _validate_items(items: list[dict[str, Any]]) -> None:
    if not items:
        raise ValidationError("items must not be empty")

    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("each item must be a dict")

        if "sku" not in item or "qty" not in item or "unit_price" not in item:
            raise ValidationError("item missing required fields")

        sku = item["sku"]
        qty = item["qty"]
        unit_price = item["unit_price"]

        if not isinstance(sku, str):
            raise ValidationError("item.sku must be a str")

        if not isinstance(qty, int) or isinstance(qty, bool):
            raise ValidationError("item.qty must be an int")

        if not isinstance(unit_price, (int, float)) or isinstance(unit_price, bool):
            raise ValidationError("item.unit_price must be a float")


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key is not None and idempotency_key in _IDEMPOTENCY:
        existing_id = _IDEMPOTENCY[idempotency_key]
        return get_order(existing_id)

    _validate_items(items)

    order = Order(
        id=uuid.uuid4().hex,
        user_id=user_id,
        items=items,
        status="pending",
        created_at=time.time(),
    )

    _STORE.put(order.id, order)

    if idempotency_key is not None:
        _IDEMPOTENCY[idempotency_key] = order.id

    return order


def get_order(order_id: str) -> Order:
    try:
        return _STORE.get(order_id)
    except KeyError:
        raise OrderNotFound(f"no order with id {order_id!r}")


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)

    if order.status != "pending":
        raise InvalidTransition(
            f"cannot cancel order in status {order.status!r}"
        )

    order.status = "cancelled"
    _STORE.put(order.id, order)
    return order


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)

    user_id = verify_token(token)
    if user_id != order.user_id:
        raise Forbidden("token does not belong to the order owner")

    if order.status != "pending":
        raise InvalidTransition(
            f"cannot pay order in status {order.status!r}"
        )

    order.status = "paid"
    _STORE.put(order.id, order)
    return order


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)

    if order.status != "paid":
        raise InvalidTransition(
            f"cannot ship order in status {order.status!r}"
        )

    order.status = "shipped"
    _STORE.put(order.id, order)
    return order


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
    global _STORE
    _STORE = MemoryStore()
    _IDEMPOTENCY.clear()