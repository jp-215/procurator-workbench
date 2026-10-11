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
        return round(
            sum(item["qty"] * item["unit_price"] for item in self.items), 2
        )


_STORE: MemoryStore = MemoryStore()
_IDEMPOTENCY: MemoryStore = MemoryStore()

# Strict state machine: (current_status) -> (action -> next_status)
_TRANSITIONS: dict[str, dict[str, str]] = {
    "pending": {"pay": "paid", "cancel": "cancelled"},
    "paid": {"ship": "shipped"},
}


def _validate_items(items: list[dict[str, Any]] | None) -> None:
    if not items:
        raise ValidationError("items must be a non-empty list")
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("each item must be a dict")
        for required in ("sku", "qty", "unit_price"):
            if required not in item:
                raise ValidationError(f"item missing required field {required!r}")


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if idempotency_key is not None:
        try:
            existing_id = _IDEMPOTENCY.get(idempotency_key)
        except KeyError:
            existing_id = None
        if existing_id is not None:
            return _STORE.get(existing_id)

    _validate_items(items)

    order = Order(
        id=str(uuid.uuid4()),
        user_id=user_id,
        items=list(items),
        status="pending",
        created_at=time.time(),
    )
    _STORE.put(order.id, order)

    if idempotency_key is not None:
        _IDEMPOTENCY.put(idempotency_key, order.id)

    return order


def get_order(order_id: str) -> Order:
    try:
        return _STORE.get(order_id)
    except KeyError:
        raise OrderNotFound(f"No order with id {order_id!r}") from None


def _transition(order_id: str, action: str, new_status: str) -> Order:
    order = get_order(order_id)
    allowed = _TRANSITIONS.get(order.status, {})
    if allowed.get(action) != new_status:
        raise InvalidTransition(
            f"Cannot {action} order {order_id!r} in status {order.status!r}"
        )
    order.status = new_status
    _STORE.put(order.id, order)
    return order


def cancel_order(order_id: str) -> Order:
    return _transition(order_id, "cancel", "cancelled")


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = auth.verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden(
            f"User {token_user_id!r} is not permitted to pay order {order_id!r}"
        )
    return _transition(order_id, "pay", "paid")


def ship_order(order_id: str) -> Order:
    return _transition(order_id, "ship", "shipped")


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    results = []
    for order in _STORE.values():
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        results.append(order)
    return results


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    global _STORE, _IDEMPOTENCY
    _STORE = MemoryStore()
    _IDEMPOTENCY = MemoryStore()