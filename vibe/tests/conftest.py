import os

# Must be set before the app modules are imported.
os.environ.setdefault("ROOMAPI_PBKDF2_ITERATIONS", "1000")
os.environ.setdefault("ROOMAPI_SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")

from datetime import datetime, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.cli import create_admin  # noqa: E402
from app.main import create_app  # noqa: E402


PASSWORD = "Corr3ct-horse"
ADMIN_PASSWORD = "Adm1n-battery"
HELSINKI = ZoneInfo("Europe/Helsinki")


@pytest.fixture
def db_file(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_file):
    with TestClient(create_app(db_file)) as c:
        yield c


def register_and_login(client, username, password=PASSWORD):
    r = client.post("/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201, r.text
    return login(client, username, password)


def login(client, username, password=PASSWORD):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def user(client):
    return register_and_login(client, "alice")


@pytest.fixture
def other_user(client):
    return register_and_login(client, "bob")


@pytest.fixture
def admin(client, db_file):
    create_admin(db_file, "admin", ADMIN_PASSWORD)
    return login(client, "admin", ADMIN_PASSWORD)


@pytest.fixture
def room(client, admin):
    r = client.post("/rooms", json={"name": "Aurora", "capacity": 8, "location": "2nd floor"}, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def slot(hour: float, duration_hours: float = 1):
    """A slot tomorrow starting at `hour` o'clock Finnish time, as offset-aware ISO strings."""
    base = (datetime.now(HELSINKI) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = base + timedelta(hours=hour)
    return start.isoformat(), (start + timedelta(hours=duration_hours)).isoformat()
