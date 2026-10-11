"""Exception taxonomy. Do not rename — the spec references these names."""
from __future__ import annotations


class OrderServiceError(Exception):
    """Base class for all ordersvc exceptions."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message)
        self.message = message


class TokenExpired(OrderServiceError):
    pass


class TokenRevoked(OrderServiceError):
    pass


class ValidationError(OrderServiceError):
    pass


class OrderNotFound(OrderServiceError):
    pass


class InvalidTransition(OrderServiceError):
    pass


class Forbidden(OrderServiceError):
    pass


class TransientError(OrderServiceError):
    pass
