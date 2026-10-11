"""ordersvc — implement per SPEC.md. Graded by a hidden acceptance suite.

Re-exports all public names so imports work either as
``from ordersvc.auth import issue_token`` or ``from ordersvc import issue_token``.
"""
from __future__ import annotations

from ordersvc.errors import (  # noqa: F401
    OrdersError,
    TokenExpired,
    TokenRevoked,
    InvalidToken,
    ValidationError,
    OrderNotFound,
    InvalidTransition,
    Forbidden,
    TransientError,
)
from ordersvc.auth import (  # noqa: F401
    issue_token,
    verify_token,
    revoke_token,
)
from ordersvc.orders import (  # noqa: F401
    Order,
    create_order,
    get_order,
    cancel_order,
    pay_order,
    ship_order,
    list_orders,
)
from ordersvc.pagination import (  # noqa: F401
    Page,
    paginate,
)
from ordersvc.retry import (  # noqa: F401
    retry_with_backoff,
)
from ordersvc.store import (  # noqa: F401
    MemoryStore,
)

__all__ = [
    # errors
    "OrdersError",
    "TokenExpired",
    "TokenRevoked",
    "InvalidToken",
    "ValidationError",
    "OrderNotFound",
    "InvalidTransition",
    "Forbidden",
    "TransientError",
    # auth
    "issue_token",
    "verify_token",
    "revoke_token",
    # orders
    "Order",
    "create_order",
    "get_order",
    "cancel_order",
    "pay_order",
    "ship_order",
    "list_orders",
    # pagination
    "Page",
    "paginate",
    # retry
    "retry_with_backoff",
    # store
    "MemoryStore",
]