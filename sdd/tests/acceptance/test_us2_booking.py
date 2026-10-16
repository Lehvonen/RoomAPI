"""User Story 2 - Book a room (FR-011, FR-012, FR-013, FR-017, NFR-004). Black-box unless marked."""

from datetime import datetime, timedelta, timezone

import pytest

from .. import conftest
from ..conftest import book, create_room, helsinki, helsinki_date

in_process_only = pytest.mark.skipif(conftest.external(), reason="sets up an inactive room directly")


def parse_z(value: str) -> datetime:
    assert value.endswith("Z"), value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# --- Scenario 1 / FR-011, FR-017: a valid booking -----------------------------------


def test_book_free_slot(client, user, room):
    r = book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["room_id"] == room["id"]
    assert body["room_name"] == room["name"]
    assert body["status"] == "active"
    assert parse_z(body["start_time"]) == datetime.fromisoformat(helsinki(1, 10))
    assert parse_z(body["end_time"]) == datetime.fromisoformat(helsinki(1, 11))


def test_offset_input_returned_as_utc(client, user, room):
    day = helsinki_date(2).isoformat()
    r = book(client, user, room["id"], f"{day}T09:00:00+03:00", f"{day}T10:00:00+03:00")
    if r.status_code == 422:  # winter time: +03:00 is outside opening hours by an hour, so use +02:00
        r = book(client, user, room["id"], f"{day}T09:00:00+02:00", f"{day}T10:00:00+02:00")
    assert r.status_code == 201, r.text
    assert r.json()["start_time"].endswith("Z")


# --- Scenarios 2, 3 / FR-013: no overlaps, back-to-back allowed ---------------------


def test_overlapping_booking_refused(client, user, other_user, room):
    assert book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 201
    r = book(client, other_user, room["id"], helsinki(1, 10, 30), helsinki(1, 11, 30))
    assert r.status_code == 409
    assert r.json()["detail"]


@pytest.mark.parametrize("start, end", [((9, 0), (12, 0)), ((10, 15), (10, 45)), ((9, 30), (10, 30))])
def test_any_overlap_shape_refused(client, user, other_user, room, start, end):
    assert book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 201
    assert book(client, other_user, room["id"], helsinki(1, *start), helsinki(1, *end)).status_code == 409


def test_back_to_back_bookings_allowed(client, user, other_user, room):
    assert book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 201
    assert book(client, other_user, room["id"], helsinki(1, 11), helsinki(1, 12)).status_code == 201
    assert book(client, other_user, room["id"], helsinki(1, 9), helsinki(1, 10)).status_code == 201


def test_same_slot_in_another_room_allowed(client, db_path, admin, user, room):
    other_room = create_room(client, db_path, admin)
    assert book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 201
    assert book(client, user, other_room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 201


# --- Scenario 4 / FR-011: order, past, horizon -------------------------------------


def test_end_not_after_start_refused(client, user, room):
    assert book(client, user, room["id"], helsinki(1, 11), helsinki(1, 10)).status_code == 422
    assert book(client, user, room["id"], helsinki(1, 10), helsinki(1, 10)).status_code == 422


def test_start_in_past_refused(client, user, room):
    r = book(client, user, room["id"], helsinki(-1, 10), helsinki(-1, 11))
    assert r.status_code == 422
    assert "past" in r.json()["detail"].lower()


def test_horizon_90_days(client, user, room):
    assert book(client, user, room["id"], helsinki(89, 10), helsinki(89, 11)).status_code == 201
    r = book(client, user, room["id"], helsinki(91, 10), helsinki(91, 11))
    assert r.status_code == 422
    assert "90 days" in r.json()["detail"]


# --- FR-012: opening hours and maximum length ----------------------------------------


def test_within_opening_hours_and_four_hours_accepted(client, user, room):
    assert book(client, user, room["id"], helsinki(1, 8), helsinki(1, 12)).status_code == 201


@pytest.mark.parametrize(
    "start, end, rule",
    [
        ((1, 7, 30), (1, 8, 30), "08:00"),
        ((1, 17, 0), (1, 18, 30), "08:00"),
        ((1, 9, 0), (1, 13, 30), "4 hours"),
        ((1, 17, 0), (2, 9, 0), "4 hours"),
    ],
)
def test_booking_rules_refused_with_message(client, user, room, start, end, rule):
    r = book(client, user, room["id"], helsinki(*start), helsinki(*end))
    assert r.status_code == 422
    assert rule in r.json()["detail"]


# --- FR-017: offsets are required -----------------------------------------------------


def test_time_without_offset_refused(client, user, room):
    day = helsinki_date(1).isoformat()
    r = book(client, user, room["id"], f"{day}T10:00:00", f"{day}T11:00:00")
    assert r.status_code == 422


# --- Room must exist and be active ------------------------------------------------------


def test_missing_room_refused(client, user):
    r = book(client, user, 999_999, helsinki(1, 10), helsinki(1, 11))
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()  # not just "Not Found" from a missing route


@in_process_only
def test_inactive_room_refused(client, db_path, admin, user):
    closed = create_room(client, db_path, admin, active=False)
    r = book(client, user, closed["id"], helsinki(1, 10), helsinki(1, 11))
    assert r.status_code == 404
    assert "room" in r.json()["detail"].lower()


# --- NFR-004 / NFR-002: bad input never gives 500; token required ------------------------


def test_far_future_date_gives_422_not_500(client, user, room):
    r = book(client, user, room["id"], "9999-12-31T23:00:00-05:00", "9999-12-31T23:30:00-05:00")
    assert r.status_code == 422
    assert r.json()["detail"]


def test_huge_room_id_gives_422(client, user):
    assert book(client, user, 2**70, helsinki(1, 10), helsinki(1, 11)).status_code == 422


def test_booking_needs_token(client, room):
    assert book(client, {}, room["id"], helsinki(1, 10), helsinki(1, 11)).status_code == 401


def test_booking_belongs_to_the_booker(client, user, room):
    me = client.get("/users/me", headers=user).json()
    r = book(client, user, room["id"], helsinki(1, 10), helsinki(1, 11))
    assert r.json()["user_id"] == me["id"]
    assert parse_z(r.json()["created_at"]) <= datetime.now(timezone.utc) + timedelta(seconds=5)
