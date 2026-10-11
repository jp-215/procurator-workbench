"""Exception taxonomy. Do not rename — the spec references these names."""


class OrderSvcError(Exception):
    """Common base for all package-specific exceptions."""
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


class TransientError(OrderSvcError, Exception):
    """May also be treated as a plain Exception subclass by consumers."""
    pass