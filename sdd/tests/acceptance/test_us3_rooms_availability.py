"""User Story 3 - See rooms and availability (FR-007, FR-010). Black-box unless marked."""

from datetime import datetime, time, timezone

import pytest

from .. import conftest
from ..conftest import HELSINKI, book, create_room, helsinki, helsinki_date

in_process_only = pytest.mark.skipif(conftest.external(), reason="uses fixed room names, which could collide on a shared server")


def utc_z(day_offset: int, hh: int, mm: int = 0) -> str:
    """Helsinki wall-clock time on that day, written as the API returns it: UTC with Z."""
    local = datetime.combine(helsinki_date(day_offset), time(hh, mm), tzinfo=HELSINKI)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slots(items: list[dict]) -> list[tuple[str, str]]:
    return [(s["start"], s["end"]) for s in items]


# --- Scenario 1 / FR-007: list and get active rooms ----------------------------------


@in_process_only
def test_list_shows_only_active_rooms_by_name(client, db_path, admin, user):
    create_room(client, db_path, admin, name="Zeta")
    create_room(client, db_path, admin, name="Alpha")
    create_room(client, db_path, admin, name="Closed", active=False)
    r = client.get("/rooms", headers=user)
    assert r.status_code == 200
    assert [room["name"] for room in r.json()] == ["Alpha", "Zeta"]


def test_list_includes_new_room_with_its_details(client, user, room):
    listed = {r["id"]: r for r in client.get("/rooms", headers=user).json()}
    assert room["id"] in listed
    assert {"name", "capacity", "location", "is_active"} <= set(listed[room["id"]])


def test_get_active_room(client, user, room):
    r = client.get(f"/rooms/{room['id']}", headers=user)
    assert r.status_code == 200
    assert r.json()["name"] == room["name"]


def test_inactive_room_hidden_from_users(client, db_path, admin, user):
    closed = create_room(client, db_path, admin, active=False)
    r = client.get(f"/rooms/{closed['id']}", headers=user)
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()


def test_missing_room_404(client, user):
    r = client.get("/rooms/999999", headers=user)
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()


def test_rooms_need_token(client):
    assert client.get("/rooms").status_code == 401


def test_huge_room_id_gives_422(client, user):
    assert client.get(f"/rooms/{2**70}", headers=user).status_code == 422


# --- Scenario 2 / FR-010: availability within opening hours ---------------------------


def availability(client, headers, room_id, day_offset):
    return client.get(f"/rooms/{room_id}/availability", params={"date": helsinki_date(day_offset).isoformat()},
                      headers=headers)


def test_empty_day_is_free_during_opening_hours(client, user, room):
    r = availability(client, user, room["id"], 2)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["date"] == helsinki_date(2).isoformat()
    assert body["opens_at"] == utc_z(2, 8)
    assert body["closes_at"] == utc_z(2, 18)
    assert body["booked"] == []
    assert slots(body["free"]) == [(utc_z(2, 8), utc_z(2, 18))]


def test_one_booking_splits_the_free_time(client, user, room):
    assert book(client, user, room["id"], helsinki(2, 10), helsinki(2, 11)).status_code == 201
    body = availability(client, user, room["id"], 2).json()
    assert slots(body["booked"]) == [(utc_z(2, 10), utc_z(2, 11))]
    assert slots(body["free"]) == [(utc_z(2, 8), utc_z(2, 10)), (utc_z(2, 11), utc_z(2, 18))]


def test_two_bookings_give_three_free_intervals(client, user, other_user, room):
    assert book(client, user, room["id"], helsinki(2, 13), helsinki(2, 14)).status_code == 201
    assert book(client, other_user, room["id"], helsinki(2, 10), helsinki(2, 11)).status_code == 201
    body = availability(client, user, room["id"], 2).json()
    assert slots(body["booked"]) == [(utc_z(2, 10), utc_z(2, 11)), (utc_z(2, 13), utc_z(2, 14))]
    assert slots(body["free"]) == [
        (utc_z(2, 8), utc_z(2, 10)),
        (utc_z(2, 11), utc_z(2, 13)),
        (utc_z(2, 14), utc_z(2, 18)),
    ]


def test_booking_at_opening_and_closing_leaves_no_edge_gaps(client, user, room):
    assert book(client, user, room["id"], helsinki(2, 8), helsinki(2, 9)).status_code == 201
    assert book(client, user, room["id"], helsinki(2, 17), helsinki(2, 18)).status_code == 201
    body = availability(client, user, room["id"], 2).json()
    assert slots(body["free"]) == [(utc_z(2, 9), utc_z(2, 17))]


def test_other_days_bookings_not_shown(client, user, room):
    assert book(client, user, room["id"], helsinki(3, 10), helsinki(3, 11)).status_code == 201
    assert availability(client, user, room["id"], 2).json()["booked"] == []


@pytest.mark.parametrize("params", [{}, {"date": "not-a-date"}, {"date": "2026-13-01"}])
def test_bad_or_missing_date_gives_422(client, user, room, params):
    r = client.get(f"/rooms/{room['id']}/availability", params=params, headers=user)
    assert r.status_code == 422


def test_availability_of_missing_room_404(client, user):
    r = availability(client, user, 999999, 2)
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()  # not just "Not Found" from a missing route


def test_availability_of_inactive_room_404(client, db_path, admin, user):
    closed = create_room(client, db_path, admin, active=False)
    r = availability(client, user, closed["id"], 2)
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()
