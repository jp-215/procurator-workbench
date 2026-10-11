"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from ordersvc.errors import InvalidToken, TokenExpired, TokenRevoked


@dataclass
class _TokenRecord:
    user_id: str
    expiry: float
    revoked: bool = False


# Module-level registry mapping opaque token string -> _TokenRecord
_REGISTRY: dict[str, _TokenRecord] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_urlsafe(32)
    expiry = now + ttl_seconds
    _REGISTRY[token] = _TokenRecord(user_id=user_id, expiry=expiry, revoked=False)
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()

    record = _REGISTRY.get(token)
    if record is None:
        raise InvalidToken(f"unknown token: {token!r}")

    if record.revoked:
        raise TokenRevoked(f"token revoked: {token!r}")

    if now > record.expiry:
        raise TokenExpired(f"token expired: {token!r}")

    return record.user_id


def revoke_token(token: str) -> None:
    record = _REGISTRY.get(token)
    if record is None:
        # Idempotent: revoking an unknown token is a no-op.
        return
    record.revoked = True


def _reset() -> None:
    """Test hook: clear all issued/revoked tokens."""
    _REGISTRY.clear()