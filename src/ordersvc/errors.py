"""Exception taxonomy. Do not rename — the spec references these names."""


class OrderSvcError(Exception):
    """Base exception for all ordersvc errors."""
    pass


class TokenExpired(OrderSvcError):
    pass


class TokenRevoked(OrderSvcError):
    pass


class ValidationError(OrderSvcError):
    pass


class OrderNotFound(OrderSvcError):
    pass


class InvalidTransition(OrderSvcError):
    pass


class Forbidden(OrderSvcError):
    pass


class TransientError(OrderSvcError):
    passss


class Forbidden(OrderSvcError):
    pass


class TransientError(OrderSvcError):
    pass
