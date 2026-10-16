import math
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from ..config import LOGIN_MAX_FAILURES_PER_IP, LOGIN_MAX_FAILURES_PER_USER, LOGIN_WINDOW
from ..db import from_db, get_db, now_utc, to_db
from ..schemas import Token, UserCreate, UserOut
from ..security import create_access_token, get_current_user, hash_password, verify_password_or_dummy

router = APIRouter(tags=["auth"])


def user_out(row: sqlite3.Row) -> UserOut:
    return UserOut(
        id=row["id"],
        username=row["username"],
        is_admin=bool(row["is_admin"]),
        created_at=from_db(row["created_at"]),
    )


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, 0, ?)",
            (body.username, hash_password(body.password), to_db(now_utc())),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    row = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return user_out(row)


def lockout_seconds(db: sqlite3.Connection, column: str, value: str, limit: int) -> int:
    """Seconds until another login attempt is allowed for this username/IP (0 = allowed now)."""
    now = now_utc()
    # The limit-th most recent failure inside the window; the block lifts when it ages out.
    row = db.execute(
        f"SELECT attempted_at FROM failed_logins WHERE {column} = ? AND attempted_at > ?"
        " ORDER BY attempted_at DESC LIMIT 1 OFFSET ?",
        (value, to_db(now - LOGIN_WINDOW), limit - 1),
    ).fetchone()
    if row is None:
        return 0
    return max(1, math.ceil((from_db(row["attempted_at"]) + LOGIN_WINDOW - now).total_seconds()))


@router.post("/auth/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    """Log in with form fields `username` and `password`; returns a bearer token.

    After too many failed attempts for a username (or from one IP address) within the
    lockout window, further attempts get 429 until the window has passed.
    """
    ip = request.client.host if request.client else "unknown"
    wait = max(
        lockout_seconds(db, "username", form.username, LOGIN_MAX_FAILURES_PER_USER),
        lockout_seconds(db, "ip", ip, LOGIN_MAX_FAILURES_PER_IP),
    )
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )
    row = db.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
    if not verify_password_or_dummy(form.password, row["password_hash"] if row else None):
        now = now_utc()
        db.execute("DELETE FROM failed_logins WHERE attempted_at <= ?", (to_db(now - LOGIN_WINDOW),))
        db.execute(
            "INSERT INTO failed_logins (username, ip, attempted_at) VALUES (?, ?, ?)",
            (form.username, ip, to_db(now)),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db.execute("DELETE FROM failed_logins WHERE username = ?", (form.username,))
    return Token(access_token=create_access_token(row["id"]))


@router.get("/users/me", response_model=UserOut)
def me(user: sqlite3.Row = Depends(get_current_user)):
    return user_out(user)
