"""NFR-001: passwords are stored only as salted Argon2id hashes and never returned."""

import sqlite3

import pytest

from .. import conftest
from ..conftest import PASSWORD, unique

in_process_only = pytest.mark.skipif(conftest.external(), reason="reads the test database directly")


@in_process_only
def test_stored_hash_is_salted_argon2id(client, db_path):
    names = [unique("alice"), unique("bob")]
    for name in names:
        client.post("/auth/register", json={"username": name, "password": PASSWORD})
    with sqlite3.connect(db_path) as conn:
        hashes = [conn.execute("SELECT password_hash FROM users WHERE username = ?", (n,)).fetchone()[0] for n in names]
    assert all(h.startswith("$argon2id$") for h in hashes)
    assert hashes[0] != hashes[1]  # same password, different salt
    assert PASSWORD not in hashes[0]


def test_no_response_contains_the_password(client):
    name = unique("alice")
    responses = [
        client.post("/auth/register", json={"username": name, "password": PASSWORD}),
        client.post("/auth/login", data={"username": name, "password": PASSWORD}),
    ]
    token = responses[1].json()["access_token"]
    responses.append(client.get("/users/me", headers={"Authorization": f"Bearer {token}"}))
    responses.append(client.post("/auth/login", data={"username": name, "password": "Wrong-password-1"}))
    for r in responses:
        assert PASSWORD not in r.text
        assert "argon2" not in r.text.lower()
        assert "hash" not in r.text.lower()
