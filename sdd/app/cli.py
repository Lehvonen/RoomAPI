"""Operator command: the only way to create an admin (FR-006).

    python -m app.cli create-admin <username>            # prompts for the password
    python -m app.cli create-admin <username> --password <pw>

Creates the user as an admin, or promotes an existing user. Promoting also sets
the given password, so the operator knows the admin's credentials.
"""

import argparse
import getpass
import os
import re
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import init_db, make_engine
from .models import User
from .security import hash_password

MIN_PASSWORD, MAX_PASSWORD = 10, 128  # FR-002
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")  # FR-001


def create_admin(db_path: str, username: str, password: str) -> User:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-50 characters from letters, digits, _ . -")
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise ValueError(f"Password must be {MIN_PASSWORD}-{MAX_PASSWORD} characters")
    engine = make_engine(db_path)
    init_db(engine)
    try:
        with Session(engine, expire_on_commit=False) as session, session.begin():
            user = session.scalars(select(User).where(User.username == username)).first()
            if user is None:
                user = User(username=username, password_hash=hash_password(password), is_admin=True)
                session.add(user)
            else:
                user.is_admin = True
                user.password_hash = hash_password(password)
        return user
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "create-admin",
        help="create an admin user, or promote an existing user (this also resets their password)",
    )
    p.add_argument("username")
    p.add_argument("--password")
    p.add_argument("--db", default=os.environ.get("ROOMAPI_DB", "roomapi.db"))
    args = parser.parse_args(argv)

    password = args.password or getpass.getpass("Password: ")
    try:
        create_admin(args.db, args.username, password)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"{args.username} is now an admin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
