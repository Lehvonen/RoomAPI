import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

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


@router.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    """Log in with form fields `username` and `password`; returns a bearer token."""
    row = db.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
    if not verify_password_or_dummy(form.password, row["password_hash"] if row else None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(row["id"]))


@router.get("/users/me", response_model=UserOut)
def me(user: sqlite3.Row = Depends(get_current_user)):
    return user_out(user)
