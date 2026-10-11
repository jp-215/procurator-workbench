"""Exception taxonomy. Do not rename — the spec references these names."""


class OrdersvcError(Exception):
    """Base class for all ordersvc exceptions."""


class TokenExpired(OrdersvcError):
    pass


class TokenRevoked(OrdersvcError):
    pass


class ValidationError(OrdersvcError):
    pass


class OrderNotFound(OrdersvcError):
    pass


class InvalidTransition(OrdersvcError):
    pass


class Forbidden(OrdersvcError):
    pass


class TransientError(OrdersvcError):
    pass