"""Order lifecycle — see SPEC.md AC-05..AC-15."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ordersvc.errors import (
    Forbidden,
    InvalidTransition,
    OrderNotFound,
    ValidationError,
)
from ordersvc.store import MemoryStore
from ordersvc import auth


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


_STORE = MemoryStore()
_IDEMPOTENCY_KEYS: dict[str, str] = {}

_ALLOWED_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped"},
}


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key is not None and idempotency_key in _IDEMPOTENCY_KEYS:
        existing_id = _IDEMPOTENCY_KEYS[idempotency_key]
        return _STORE.get(existing_id)

    if not items:
        raise ValidationError("items must not be empty")

    order_id = str(uuid.uuid4())
    order = Order(
        id=order_id,
        user_id=user_id,
        items=list(items),
        status="pending",
        created_at=time.time(),
    )
    _STORE.put(order_id, order)

    if idempotency_key is not None:
        _IDEMPOTENCY_KEYS[idempotency_key] = order_id

    return order


def get_order(order_id: str) -> Order:
    try:
        return _STORE.get(order_id)
    except KeyError:
        raise OrderNotFound(f"unknown order: {order_id!r}")


def _transition(order: Order, new_status: str) -> Order:
    allowed = _ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise InvalidTransition(
            f"cannot transition order {order.id!r} from "
            f"{order.status!r} to {new_status!r}"
        )
    order.status = new_status
    _STORE.put(order.id, order)
    return order


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)
    return _transition(order, "cancelled")


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user = auth.verify_token(token)
    if token_user != order.user_id:
        raise Forbidden(
            f"token user {token_user!r} is not owner of order {order_id!r}"
        )
    return _transition(order, "paid")


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)
    return _transition(order, "shipped")


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
    _IDEMPOTENCY_KEYS.clear()