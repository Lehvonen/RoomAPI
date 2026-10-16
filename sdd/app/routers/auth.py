"""Registration, login and own profile (User Story 1: FR-001–FR-006)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import FailedLogin, User
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
    """Log in with form fields `username` and `password`; returns a 60-minute bearer token (FR-003)."""
    user = session.scalars(select(User).where(User.username == form.username)).first()
    if not verify_password_or_dummy(form.password, user.password_hash if user else None):
        # Recorded tidily for the login slow-down (NFR-009), whether or not the user exists.
        session.add(FailedLogin(username=form.username.lower()[:FAILED_LOGIN_USERNAME_LENGTH]))
        session.commit()
        # Same refusal for a wrong password and an unknown username (FR-004).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id, request))


@router.get("/users/me", response_model=UserOut, responses={401: {"description": "Invalid or expired token"}})
def me(user: User = Depends(get_current_user)) -> User:
    """Your own profile; never includes the password or its hash (FR-005)."""
    return user
