"""Order lifecycle — see SPEC.md AC-05..AC-15, AC-26..AC-32."""
from __future__ import annotations

import time
import uuid
from typing import Any

from ordersvc import auth
from ordersvc.errors import (
    Forbidden,
    InvalidTransition,
    OrderNotFound,
    ValidationError,
)
from ordersvc.models import Order
from ordersvc.store import MemoryStore

# Orders keyed by order id.
_orders = MemoryStore()
# Idempotency key -> order id.
_idempotency = MemoryStore()

# Recognized status values for the order status machine. `refunded` is
# recognized here (mandate v2 scope change) but no transition logic into
# or out of it beyond what is explicitly implemented below is wired yet.
_STATUSES = {"pending", "paid", "shipped", "cancelled", "refunded"}


def create_order(
    user_id: str,
    items: list[dict[str, Any]],
    idempotency_key: str | None = None,
) -> Order:
    if not items:
        raise ValidationError("items must be a non-empty list")

    if idempotency_key is not None:
        try:
            existing_id = _idempotency.get(idempotency_key)
        except KeyError:
            existing_id = None
        if existing_id is not None:
            return _orders.get(existing_id)

    order_id = str(uuid.uuid4())
    order = Order(
        id=order_id,
        user_id=user_id,
        items=list(items),
        status="pending",
        created_at=time.time(),
        idempotency_key=idempotency_key,
        refund_amount=0.0,
    )
    _orders.put(order_id, order)
    if idempotency_key is not None:
        _idempotency.put(idempotency_key, order_id)
    return order


def get_order(order_id: str) -> Order:
    try:
        return _orders.get(order_id)
    except KeyError:
        raise OrderNotFound(f"No such order: {order_id!r}")


def cancel_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "pending":
        raise InvalidTransition(
            f"Cannot cancel order {order_id!r} from status {order.status!r}"
        )
    order.status = "cancelled"
    _orders.put(order_id, order)
    return order


def pay_order(order_id: str, token: str) -> Order:
    order = get_order(order_id)
    token_user_id = auth.verify_token(token)
    if token_user_id != order.user_id:
        raise Forbidden(
            f"Token user {token_user_id!r} is not the owner of order {order_id!r}"
        )
    if order.status != "pending":
        raise InvalidTransition(
            f"Cannot pay order {order_id!r} from status {order.status!r}"
        )
    order.status = "paid"
    _orders.put(order_id, order)
    return order


def ship_order(order_id: str) -> Order:
    order = get_order(order_id)
    if order.status != "paid":
        raise InvalidTransition(
            f"Cannot ship order {order_id!r} from status {order.status!r}"
        )
    order.status = "shipped"
    _orders.put(order_id, order)
    return order


def list_orders(user_id: str | None = None, status: str | None = None) -> list[Order]:
    result = []
    for order in _orders.values():
        if user_id is not None and order.user_id != user_id:
            continue
        if status is not None and order.status != status:
            continue
        result.append(order)
    return result


def _reset() -> None:
    """Test hook: clear all stored orders and idempotency records."""
    _orders.clear()
    _idempotency.clear()