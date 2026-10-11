"""Token auth — see SPEC.md AC-01..AC-04."""
from __future__ import annotations

import secrets
import time
from typing import Dict

from ordersvc.errors import OrderSvcError, TokenExpired, TokenRevoked


class InvalidToken(OrderSvcError):
    """Raised when a token is unknown to the registry."""
    pass


class _TokenRecord:
    __slots__ = ("user_id", "expires_at", "revoked")

    def __init__(self, user_id: str, expires_at: float):
        self.user_id = user_id
        self.expires_at = expires_at
        self.revoked = False


_TOKENS: Dict[str, _TokenRecord] = {}


def issue_token(user_id: str, ttl_seconds: int = 3600, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    token = secrets.token_hex(16)
    expires_at = now + ttl_seconds
    _TOKENS[token] = _TokenRecord(user_id=user_id, expires_at=expires_at)
    return token


def verify_token(token: str, *, now: float | None = None) -> str:
    if now is None:
        now = time.time()
    record = _TOKENS.get(token)
    if record is None:
        raise InvalidToken(f"unknown token: {token!r}")
    if record.revoked:
        raise TokenRevoked(f"token revoked: {token!r}")
    if now >= record.expires_at:
        raise TokenExpired(f"token expired: {token!r}")
    return record.user_id


def revoke_token(token: str) -> None:
    record = _TOKENS.get(token)
    if record is None:
        return
    record.revoked = True


def _reset() -> None:
    """Test hook: clear all issued tokens."""
    _TOKENS.clear()