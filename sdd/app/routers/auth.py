"""Registration, login and own profile (User Story 1: FR-001–FR-006), with the login slow-down (NFR-009)."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import LOGIN_FAILURE_LIMIT, LOGIN_FAILURE_WINDOW
from ..db import get_session
from ..models import FailedLogin, User, utcnow
from ..schemas import Token, UserCreate, UserOut
from ..security import create_access_token, get_current_user, hash_password, verify_password_or_dummy

router = APIRouter(tags=["auth"])

FAILED_LOGIN_USERNAME_LENGTH = 50


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"description": "Username already taken"}})
def register(body: UserCreate, session: Session = Depends(get_session)) -> User:
    """Create a regular user. Admins are only created by the operator CLI (FR-006)."""
    user = User(username=body.username, password_hash=hash_password(body.password), is_admin=False)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken") from None
    return user


@router.post("/auth/login", response_model=Token,
             responses={401: {"description": "Incorrect username or password"}})
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    """Log in with form fields `username` and `password`; returns a 60-minute bearer token (FR-003).

    After 5 failed attempts for a username within 15 minutes, every further attempt for it
    waits 2 seconds before it is answered, right password or not. Accounts are never locked (NFR-009).
    """
    key = form.username.lower()[:FAILED_LOGIN_USERNAME_LENGTH]
    recent_failures = session.scalar(
        select(func.count(FailedLogin.id)).where(
            FailedLogin.username == key, FailedLogin.attempted_at > utcnow() - LOGIN_FAILURE_WINDOW
        )
    )
    # End this transaction before waiting, so the delay never holds the database write lock
    # and other users' requests are not slowed down.
    session.commit()
    if recent_failures >= LOGIN_FAILURE_LIMIT:
        time.sleep(request.app.state.settings.login_delay_seconds)

    user = session.scalars(select(User).where(User.username == form.username)).first()
    if not verify_password_or_dummy(form.password, user.password_hash if user else None):
        # Recorded whether or not the user exists; rows older than the window are tidied away.
        session.execute(delete(FailedLogin).where(FailedLogin.attempted_at <= utcnow() - LOGIN_FAILURE_WINDOW))
        session.add(FailedLogin(username=key))
        session.commit()
        # Same refusal for a wrong password and an unknown username (FR-004).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session.execute(delete(FailedLogin).where(FailedLogin.username == key))  # a success clears the count
    session.commit()
    return Token(access_token=create_access_token(user.id, request))


@router.get("/users/me", response_model=UserOut, responses={401: {"description": "Invalid or expired token"}})
def me(user: User = Depends(get_current_user)) -> User:
    """Your own profile; never includes the password or its hash (FR-005)."""
    return user
