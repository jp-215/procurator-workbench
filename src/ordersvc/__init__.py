"""ordersvc — implement per SPEC.md. Graded by a hidden acceptance suite."""
from ordersvc.errors import (  # noqa: F401
    OrderSvcError,
    TokenExpired,
    TokenRevoked,
    ValidationError,
    OrderNotFound,
    InvalidTransition,
    Forbidden,
    TransientError,
)