"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time

from ordersvc.errors import OrderSvcError, TokenExpired, TokenRevoked


class InvalidToken(OrderSvcError):
    """Raised for unknown or malformed tokens."""
    pass


# Module-level registry: token -> {"user_id": str, "expiry": float, "revoked": bool}
_TOKENS: dict[str, dict] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_urlsafe(32)
    while token in _TOKENS:
        token = secrets.token_urlsafe(32)
    _TOKENS[token] = {
        "user_id": user_id,
        "expiry": now + ttl_seconds,
        "revoked": False,
    }
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _TOKENS.get(token)
    if record is None:
        raise InvalidToken(f"Unknown or malformed token: {token!r}")
    if record["revoked"]:
        raise TokenRevoked(f"Token has been revoked: {token!r}")
    if now >= record["expiry"]:
        raise TokenExpired(f"Token expired at {record['expiry']}")
    return record["user_id"]


def revoke_token(token: str) -> None:
    record = _TOKENS.get(token)
    if record is None:
        raise InvalidToken(f"Unknown or malformed token: {token!r}")
    record["revoked"] = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _TOKENS.clear()