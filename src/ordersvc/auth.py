"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time

from ordersvc.errors import OrderServiceError, TokenExpired, TokenRevoked


class InvalidToken(OrderServiceError):
    pass


_registry: dict[str, dict] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_urlsafe(32)
    _registry[token] = {
        "user_id": user_id,
        "expiry": now + ttl_seconds,
        "revoked": False,
    }
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _registry.get(token)
    if record is None:
        raise InvalidToken("unknown or malformed token")
    if record["revoked"]:
        raise TokenRevoked("token has been revoked")
    if now >= record["expiry"]:
        raise TokenExpired("token has expired")
    return record["user_id"]


def revoke_token(token: str) -> None:
    record = _registry.get(token)
    if record is None:
        return
    record["revoked"] = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _registry.clear()