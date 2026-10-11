"""Exception taxonomy. Do not rename — the spec references these names."""


class OrderSvcError(Exception):
    """Base class for all ordersvc exceptions."""
    pass


# --- Auth exceptions ---

class TokenExpired(OrderSvcError):
    pass


class TokenRevoked(OrderSvcError):
    pass


class InvalidToken(OrderSvcError):
    pass


# --- Orders exceptions ---

class ValidationError(OrderSvcError):
    pass


class OrderNotFound(OrderSvcError):
    pass


class InvalidTransition(OrderSvcError):
    pass


class Forbidden(OrderSvcError):
    pass


# --- Retry exceptions ---

class TransientError(OrderSvcError):
    pass