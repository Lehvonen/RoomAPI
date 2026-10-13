"""Password hashing, JWT tokens, and the current-user / admin dependencies."""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .db import get_db, now_utc

log = logging.getLogger("roomapi")

PBKDF2_ITERATIONS = int(os.environ.get("ROOMAPI_PBKDF2_ITERATIONS", "600000"))
TOKEN_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(minutes=int(os.environ.get("ROOMAPI_TOKEN_MINUTES", "60")))

_secret = os.environ.get("ROOMAPI_SECRET_KEY")
if not _secret:
    _secret = secrets.token_urlsafe(32)
    log.warning("ROOMAPI_SECRET_KEY is not set; using a random key. Tokens will not survive a restart.")
SECRET_KEY = _secret

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, digest_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
    return hmac.compare_digest(digest, expected)


# Used to equalize login timing when the username does not exist.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def verify_password_or_dummy(password: str, stored: str | None) -> bool:
    if stored is None:
        verify_password(password, _DUMMY_HASH)
        return False
    return verify_password(password, stored)


def create_access_token(user_id: int) -> str:
    now = now_utc()
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, SECRET_KEY, algorithm=TOKEN_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise unauthorized
    return user


def require_admin(user: sqlite3.Row = Depends(get_current_user)) -> sqlite3.Row:
    if not user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
