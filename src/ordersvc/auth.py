"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import time
import uuid

from ordersvc.errors import OrderSvcError, TokenExpired, TokenRevoked


class InvalidToken(OrderSvcError):
    """Raised for unknown or malformed tokens."""
    pass


# Module-level registry: token -> dict(user_id, issued_at, ttl_seconds, revoked)
_REGISTRY: dict[str, dict] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = uuid.uuid4().hex
    _REGISTRY[token] = {
        "user_id": user_id,
        "issued_at": now,
        "ttl_seconds": ttl_seconds,
        "revoked": False,
    }
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()

    record = _REGISTRY.get(token)
    if record is None:
        raise InvalidToken("unknown or malformed token")

    if record["revoked"]:
        raise TokenRevoked("token has been revoked")

    if now >= record["issued_at"] + record["ttl_seconds"]:
        raise TokenExpired("token has expired")

    return record["user_id"]


def revoke_token(token: str) -> None:
    record = _REGISTRY.get(token)
    if record is None:
        return
    record["revoked"] = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _REGISTRY.clear()