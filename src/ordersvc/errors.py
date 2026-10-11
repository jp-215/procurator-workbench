"""Exception taxonomy. Do not rename — the spec references these names."""
from __future__ import annotations


class OrdersError(Exception):
    """Base class for all ordersvc exceptions."""


class TokenExpired(OrdersError):
    pass


class TokenRevoked(OrdersError):
    pass


class InvalidToken(OrdersError):
    pass


class ValidationError(OrdersError):
    pass


class OrderNotFound(OrdersError):
    pass


class InvalidTransition(OrdersError):
    pass


class Forbidden(OrdersError):
    pass


class TransientError(OrdersError):
    pass