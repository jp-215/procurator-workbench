"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from ordersvc.errors import TokenExpired, TokenRevoked


@dataclass
class _TokenRecord:
    user_id: str
    issued_at: float
    expires_at: float
    revoked: bool = False


_TOKENS: dict[str, _TokenRecord] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_urlsafe(32)
    _TOKENS[token] = _TokenRecord(
        user_id=user_id,
        issued_at=now,
        expires_at=now + ttl_seconds,
        revoked=False,
    )
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _TOKENS[token]  # KeyError on unknown token
    if record.revoked:
        raise TokenRevoked(f"Token {token!r} has been revoked")
    if now >= record.expires_at:
        raise TokenExpired(f"Token {token!r} expired at {record.expires_at}")
    return record.user_id


def revoke_token(token: str) -> None:
    record = _TOKENS.get(token)
    if record is not None:
        record.revoked = True


def _reset() -> None:
    """Test hook: clear all stored tokens."""
    _TOKENS.clear()