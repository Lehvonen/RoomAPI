"""User Story 1 - Register and log in (FR-001–FR-006, NFR-002). Black-box unless marked."""

import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from .. import conftest
from ..conftest import PASSWORD, login, register_and_login, unique

in_process_only = pytest.mark.skipif(conftest.external(), reason="needs the test server's database or secret")


def register(client, username, password=PASSWORD, **extra):
    return client.post("/auth/register", json={"username": username, "password": password, **extra})


# --- Scenario 1 / FR-001, FR-005: register ---------------------------------------


def test_register_creates_regular_user_without_password_in_response(client):
    name = unique("alice")
    r = register(client, name)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["username"] == name
    assert body["is_admin"] is False
    assert set(body) == {"id", "username", "is_admin", "created_at"}
    assert body["created_at"].endswith("Z")


# --- Scenario 2 / FR-001: unique regardless of case ------------------------------


def test_username_taken_regardless_of_case(client):
    name = unique("alice")
    assert register(client, name).status_code == 201
    r = register(client, name.upper())
    assert r.status_code == 409
    assert "taken" in r.json()["detail"].lower()


@pytest.mark.parametrize("name", ["ab", "a" * 51, "bad name", "bad/name", "ääkkönen"])
def test_invalid_usernames_refused(client, name):
    assert register(client, name).status_code == 422


@pytest.mark.parametrize("length", [3, 50])
def test_username_length_boundaries_accepted(client, length):
    name = (unique("u").replace("_", "") * 10)[:length]
    assert register(client, name).status_code == 201


# --- FR-002: password length -----------------------------------------------------


@pytest.mark.parametrize("length, expected", [(9, 422), (10, 201), (128, 201), (129, 422)])
def test_password_length(client, length, expected):
    assert register(client, unique("pw"), password="p" * length).status_code == expected


# --- Scenario 3 / FR-003: log in -------------------------------------------------


def test_login_returns_bearer_token_valid_for_60_minutes(client):
    name = unique("alice")
    register(client, name)
    r = client.post("/auth/login", data={"username": name, "password": PASSWORD})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert claims["exp"] - claims["iat"] == 60 * 60


def test_login_is_case_insensitive_on_username(client):
    name = unique("alice")
    register(client, name)
    assert client.post("/auth/login", data={"username": name.upper(), "password": PASSWORD}).status_code == 200


# --- Scenario 4 / FR-004: same refusal for wrong password and unknown user --------


def test_wrong_password_and_unknown_user_get_the_same_refusal(client):
    name = unique("alice")
    register(client, name)
    wrong = client.post("/auth/login", data={"username": name, "password": "Wrong-password-1"})
    unknown = client.post("/auth/login", data={"username": unique("ghost"), "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


# --- FR-005: own profile -----------------------------------------------------------


def test_profile_shows_user_and_no_password_data(client):
    name = unique("alice")
    register(client, name)
    r = client.get("/users/me", headers=login(client, name))
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == name
    assert "password" not in str(body).lower()


# --- FR-006: registration never creates an admin -------------------------------------


def test_registration_ignores_admin_request(client):
    r = register(client, unique("sneaky"), is_admin=True)
    assert r.status_code == 201
    assert r.json()["is_admin"] is False


# --- NFR-002: protected endpoints need a valid token ---------------------------------


def test_profile_without_token_refused(client):
    assert client.get("/users/me").status_code == 401


def test_profile_with_tampered_token_refused(client, user):
    token = user["Authorization"].removeprefix("Bearer ")
    head, payload, signature = token.split(".")
    tampered = f"{head}.{payload}.{signature[::-1]}"
    assert client.get("/users/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401


@in_process_only
def test_profile_with_expired_token_refused(client, user):
    token = user["Authorization"].removeprefix("Bearer ")
    claims = jwt.decode(token, options={"verify_signature": False})
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    expired = jwt.encode(
        {"sub": claims["sub"], "iat": past, "exp": past + timedelta(minutes=60)},
        conftest.os.environ["ROOMAPI_SECRET_KEY"],
        algorithm="HS256",
    )
    assert client.get("/users/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


# --- Failed logins are recorded tidily (input to NFR-009) ----------------------------


@in_process_only
def test_failed_login_username_stored_lower_case_and_at_most_50_characters(client, db_path):
    client.post("/auth/login", data={"username": "MiXeD-Case-User", "password": "Wrong-password-1"})
    client.post("/auth/login", data={"username": "Z" * 80, "password": "Wrong-password-1"})
    with sqlite3.connect(db_path) as conn:
        stored = [row[0] for row in conn.execute("SELECT username FROM failed_logins ORDER BY id")]
    assert stored == ["mixed-case-user", "z" * 50]


def test_successful_login_after_register_helper(client):
    assert client.get("/users/me", headers=register_and_login(client)).status_code == 200
