"""User Story 4 - See and cancel my bookings (FR-014, FR-015, FR-016). Black-box unless marked."""

import pytest

from .. import conftest
from ..conftest import book, booking_row, helsinki, helsinki_date, insert_ended_booking, login, unique

in_process_only = pytest.mark.skipif(conftest.external(), reason="reads or writes the test database directly")


def my_bookings(client, headers):
    r = client.get("/bookings/me", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# --- Scenario 1 / FR-014: only my upcoming bookings, oldest first ---------------------


def test_list_shows_only_my_bookings_oldest_first(client, user, other_user, room):
    later = book(client, user, room["id"], helsinki(3, 10), helsinki(3, 11)).json()
    earlier = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    book(client, other_user, room["id"], helsinki(2, 12), helsinki(2, 13))
    assert [b["id"] for b in my_bookings(client, user)] == [earlier["id"], later["id"]]


def test_list_is_empty_for_new_user(client, user):
    assert my_bookings(client, user) == []


@in_process_only
def test_list_leaves_out_ended_bookings(client, db_path, room):
    name = unique("alice")
    client.post("/auth/register", json={"username": name, "password": conftest.PASSWORD})
    headers = login(client, name)
    insert_ended_booking(db_path, room["id"], name)
    upcoming = book(client, headers, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    assert [b["id"] for b in my_bookings(client, headers)] == [upcoming["id"]]


def test_list_needs_token(client):
    assert client.get("/bookings/me").status_code == 401


# --- Scenario 2 / FR-015: cancel my booking; the slot is freed ------------------------


def test_cancel_own_booking_frees_the_slot(client, user, other_user, room):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    assert client.delete(f"/bookings/{booking['id']}", headers=user).status_code == 204
    assert my_bookings(client, user) == []
    # The cancelled booking no longer blocks its slot, for bookings or availability (FR-013).
    assert book(client, other_user, room["id"], helsinki(2, 10), helsinki(2, 11)).status_code == 201
    params = {"date": helsinki_date(2).isoformat()}
    booked = client.get(f"/rooms/{room['id']}/availability", params=params, headers=user).json()["booked"]
    assert len(booked) == 1


@in_process_only
def test_cancelled_booking_is_kept_with_who_and_when(client, db_path, user, room):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    client.delete(f"/bookings/{booking['id']}", headers=user)
    row = booking_row(db_path, booking["id"])
    assert row["status"] == "cancelled"
    assert row["cancelled_at"] is not None
    assert row["cancelled_by"] == booking["user_id"]


def test_cancel_twice_refused(client, user, room):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    assert client.delete(f"/bookings/{booking['id']}", headers=user).status_code == 204
    r = client.delete(f"/bookings/{booking['id']}", headers=user)
    assert r.status_code == 409
    assert "cancelled" in r.json()["detail"].lower()


@in_process_only
def test_cancel_ended_booking_refused_for_user(client, db_path, room):
    name = unique("alice")
    client.post("/auth/register", json={"username": name, "password": conftest.PASSWORD})
    headers = login(client, name)
    ended = insert_ended_booking(db_path, room["id"], name)
    r = client.delete(f"/bookings/{ended}", headers=headers)
    assert r.status_code == 409
    assert "ended" in r.json()["detail"].lower()


# --- Scenario 3 / NFR-003: someone else's booking ------------------------------------------


def test_cancel_someone_elses_booking_forbidden(client, user, other_user, room):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    r = client.delete(f"/bookings/{booking['id']}", headers=other_user)
    assert r.status_code == 403
    assert [b["id"] for b in my_bookings(client, user)] == [booking["id"]]


def test_cancel_missing_booking_404(client, user):
    r = client.delete("/bookings/999999", headers=user)
    assert r.status_code == 404
    assert "booking" in r.json()["detail"].lower()


def test_cancel_huge_id_gives_422(client, user):
    assert client.delete(f"/bookings/{2**70}", headers=user).status_code == 422


def test_cancel_needs_token(client, user, room):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    assert client.delete(f"/bookings/{booking['id']}").status_code == 401


# --- FR-016: bookings can't be edited -------------------------------------------------------


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_no_edit_endpoint(client, user, room, method):
    booking = book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).json()
    r = client.request(method, f"/bookings/{booking['id']}", json={"start_time": helsinki(2, 12)}, headers=user)
    assert r.status_code == 405
