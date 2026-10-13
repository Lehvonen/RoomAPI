"""Admin bootstrap.

    python -m app.cli create-admin <username>         # prompts for a password
    python -m app.cli create-admin <username> --password <pw>

Creates the user as an admin, or promotes an existing user to admin.
"""

import argparse
import getpass
import sys

from .db import connect, db_path, init_db, now_utc, to_db
from .schemas import UserCreate
from .security import hash_password


def create_admin(path: str, username: str, password: str | None) -> str:
    init_db(path)
    conn = connect(path)
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (existing["id"],))
            return f"Promoted existing user '{username}' to admin."
        if password is None:
            password = getpass.getpass("Password: ")
        UserCreate(username=username, password=password)  # same rules as registration
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, 1, ?)",
            (username, hash_password(password), to_db(now_utc())),
        )
        return f"Created admin user '{username}'."
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-admin", help="Create an admin user or promote an existing one")
    p.add_argument("username")
    p.add_argument("--password", help="Omit to be prompted (ignored when promoting an existing user)")
    p.add_argument("--db", default=None, help="SQLite file (default: $ROOMAPI_DB or ./roomapi.db)")
    args = parser.parse_args(argv)

    try:
        print(create_admin(args.db or db_path(), args.username, args.password))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
