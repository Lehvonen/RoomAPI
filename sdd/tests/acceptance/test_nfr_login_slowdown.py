"""NFR-009: after 5 failed logins for a username within 15 minutes, further attempts wait 2 seconds.
Accounts are never locked, and one user's failures never slow anyone else down."""

import threading
import time
from dataclasses import replace

import pytest

from .. import conftest
from ..conftest import PASSWORD, unique

DELAY = 2.0  # the spec's delay; in-process the app is set to it, an external server must use its default
FAST = 1.0  # an undelayed login (Argon2 included) is well under this


@pytest.fixture
def slow_client(client):
    if not conftest.external():
        client.app.state.settings = replace(client.app.state.settings, login_delay_seconds=DELAY)
    return client


def registered(client) -> str:
    name = unique("alice")
    assert client.post("/auth/register", json={"username": name, "password": PASSWORD}).status_code == 201
    return name


def attempt(client, username, password="Wrong-password-1"):
    start = time.perf_counter()
    r = client.post("/auth/login", data={"username": username, "password": password})
    return r, time.perf_counter() - start


def fail(client, username, times):
    for _ in range(times):
        r, elapsed = attempt(client, username)
        assert r.status_code == 401
        assert elapsed < FAST, f"attempt slowed down too early ({elapsed:.2f}s)"


def test_sixth_failure_within_15_minutes_is_delayed(slow_client):
    name = registered(slow_client)
    fail(slow_client, name, 5)
    r, elapsed = attempt(slow_client, name)
    assert r.status_code == 401
    assert elapsed >= DELAY


def test_correct_password_still_logs_in_after_many_failures(slow_client):
    name = registered(slow_client)
    fail(slow_client, name, 5)
    attempt(slow_client, name)  # 6th failure, delayed
    r, elapsed = attempt(slow_client, name, PASSWORD)
    assert r.status_code == 200  # never locked out (no N1)
    assert elapsed >= DELAY  # the delay applies whether the password is right or not


def test_successful_login_clears_the_failures(slow_client):
    name = registered(slow_client)
    fail(slow_client, name, 5)
    r, _ = attempt(slow_client, name, PASSWORD)
    assert r.status_code == 200
    r, elapsed = attempt(slow_client, name)
    assert r.status_code == 401
    assert elapsed < FAST


def test_failures_count_regardless_of_letter_case(slow_client):
    name = registered(slow_client)
    fail(slow_client, name.upper(), 5)
    _, elapsed = attempt(slow_client, name)
    assert elapsed >= DELAY


def test_failures_for_other_usernames_do_not_slow_a_user(slow_client):
    """20 failures for non-existent usernames from one client must not affect anyone else (no N1b)."""
    name = registered(slow_client)
    for i in range(20):
        attempt(slow_client, unique(f"ghost{i}"))
    r, elapsed = attempt(slow_client, name, PASSWORD)
    assert r.status_code == 200
    assert elapsed < FAST


def test_a_delayed_login_does_not_block_other_requests(slow_client):
    """The 2-second wait must not hold the database lock, or every other request would stall too."""
    victim, bystander = registered(slow_client), registered(slow_client)
    fail(slow_client, victim, 5)
    delayed = threading.Thread(target=attempt, args=(slow_client, victim))
    delayed.start()
    time.sleep(0.3)  # the victim's request is now waiting out its delay
    r, elapsed = attempt(slow_client, bystander, PASSWORD)
    delayed.join()
    assert r.status_code == 200
    assert elapsed < FAST, f"bystander waited {elapsed:.2f}s behind the delayed login"
