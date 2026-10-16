"""User Story 5 - Manage rooms and bookings as admin (FR-008, FR-009, FR-015, NFR-003). Black-box unless marked."""

import pytest

from .. import conftest
from ..conftest import PASSWORD, book, booking_row, helsinki, insert_ended_booking, login, unique

in_process_only = pytest.mark.skipif(conftest.external(), reason="reads or writes the test database directly")


def create(client, headers, **body):
    body.setdefault("name", unique("room"))
    body.setdefault("capacity", 8)
    return client.post("/rooms", json=body, headers=headers)


# --- Scenario 1 / FR-008: create ---------------------------------------------------------


def test_admin_creates_active_room(client, admin):
    name = unique("Aurora")
    r = create(client, admin, name=name, capacity=12, location="2nd floor", description="Screen and whiteboard")
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["name"], body["capacity"], body["location"], body["is_active"]) == (name, 12, "2nd floor", True)
    assert body["created_at"].endswith("Z")


@pytest.mark.parametrize(
    "field, value",
    [("capacity", 0), ("capacity", 10_001), ("name", ""), ("name", "x" * 101),
     ("location", "x" * 201), ("description", "x" * 2001)],
)
def test_invalid_room_fields_refused(client, admin, field, value):
    assert create(client, admin, **{field: value}).status_code == 422


# --- Scenario 2 / FR-008: names unique regardless of case ----------------------------------


def test_duplicate_name_refused_on_create(client, admin):
    name = unique("Aurora")
    assert create(client, admin, name=name).status_code == 201
    r = create(client, admin, name=name.upper())
    assert r.status_code == 409
    assert "name" in r.json()["detail"].lower()


def test_duplicate_name_refused_on_rename(client, admin):
    first = create(client, admin, name=unique("Aurora")).json()
    second = create(client, admin).json()
    r = client.patch(f"/rooms/{second['id']}", json={"name": first["name"].lower()}, headers=admin)
    assert r.status_code == 409


# --- FR-008: edit ----------------------------------------------------------------------------


def test_admin_edits_room(client, admin):
    room = create(client, admin).json()
    new_name = unique("Borealis")
    r = client.patch(f"/rooms/{room['id']}", json={"name": new_name, "capacity": 20, "location": None}, headers=admin)
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["name"], body["capacity"], body["location"]) == (new_name, 20, None)


@pytest.mark.parametrize("body", [{"name": None}, {"capacity": None}, {"is_active": None}, {"capacity": 0}])
def test_invalid_edits_refused(client, admin, body):
    room = create(client, admin).json()
    assert client.patch(f"/rooms/{room['id']}", json=body, headers=admin).status_code == 422


def test_edit_missing_room_404(client, admin):
    r = client.patch("/rooms/999999", json={"capacity": 3}, headers=admin)
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()


def test_edit_huge_room_id_gives_422(client, admin):
    assert client.patch(f"/rooms/{2**70}", json={"capacity": 3}, headers=admin).status_code == 422


# --- Scenario 3 / FR-009: deactivate, refused while bookings exist ----------------------------


def test_deactivation_refused_while_future_booking_exists(client, admin, user):
    room = create(client, admin).json()
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    r = client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin)
    assert r.status_code == 409
    assert "1" in r.json()["detail"]  # the refusal says how many bookings block it
    assert client.delete(f"/bookings/{booking['id']}", headers=admin).status_code == 204
    assert client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin).status_code == 200


def test_deactivated_room_hidden_and_unbookable_then_reactivated(client, admin, user):
    room = create(client, admin).json()
    assert client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin).json()["is_active"] is False
    assert room["id"] not in [r["id"] for r in client.get("/rooms", headers=user).json()]
    assert client.get(f"/rooms/{room['id']}", headers=user).status_code == 404
    assert client.get(f"/rooms/{room['id']}", headers=admin).status_code == 200  # admins still see it
    assert book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).status_code == 404

    assert client.patch(f"/rooms/{room['id']}", json={"is_active": True}, headers=admin).status_code == 200
    assert book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).status_code == 201


@in_process_only
def test_ended_bookings_do_not_block_deactivation(client, db_path, admin):
    room = create(client, admin).json()
    name = unique("alice")
    client.post("/auth/register", json={"username": name, "password": PASSWORD})
    insert_ended_booking(db_path, room["id"], name)
    assert client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin).status_code == 200


# --- Scenario 4 / FR-015: admins cancel any booking ---------------------------------------------


def test_admin_cancels_another_users_booking(client, admin, user):
    room = create(client, admin).json()
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    assert client.delete(f"/bookings/{booking['id']}", headers=admin).status_code == 204
    assert client.get("/bookings/me", headers=user).json() == []


@in_process_only
def test_admin_cancellation_records_the_admin(client, db_path, admin, user):
    room = create(client, admin).json()
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    client.delete(f"/bookings/{booking['id']}", headers=admin)
    admin_id = client.get("/users/me", headers=admin).json()["id"]
    assert booking_row(db_path, booking["id"])["cancelled_by"] == admin_id


@in_process_only
def test_admin_cancels_ended_booking(client, db_path, admin):
    room = create(client, admin).json()
    name = unique("alice")
    client.post("/auth/register", json={"username": name, "password": PASSWORD})
    ended = insert_ended_booking(db_path, room["id"], name)
    assert client.delete(f"/bookings/{ended}", headers=admin).status_code == 204
    assert booking_row(db_path, ended)["status"] == "cancelled"


# --- Scenario 5 / NFR-003: regular users refused --------------------------------------------------


def test_regular_user_cannot_create_room(client, user):
    r = create(client, user)
    assert r.status_code == 403
    assert "admin" in r.json()["detail"].lower()


def test_regular_user_cannot_edit_room(client, admin, user):
    room = create(client, admin).json()
    assert client.patch(f"/rooms/{room['id']}", json={"capacity": 1}, headers=user).status_code == 403
    assert client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=user).status_code == 403


def test_room_management_needs_token(client):
    assert client.post("/rooms", json={"name": unique("room"), "capacity": 2}).status_code == 401
