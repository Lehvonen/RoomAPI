"""NFR-004 / SC-004: no client input causes a server error; every invalid request gets a 4xx with a message."""

import pytest

from ..conftest import helsinki, unique

HUGE = 2**70
BAD_IDS = [0, -1, HUGE]
FAR = "9999-12-31T23:00:00-05:00"
FAR_END = "9999-12-31T23:30:00-05:00"


def assert_client_error(r):
    assert r.status_code != 500, r.text
    assert 400 <= r.status_code < 500, (r.status_code, r.text)
    detail = r.json().get("detail")
    assert detail, r.text  # always a message (NFR-008)


@pytest.mark.parametrize("bad_id", BAD_IDS)
@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/rooms/{id}"),
        ("GET", "/rooms/{id}/availability?date=2026-11-02"),
        ("PATCH", "/rooms/{id}"),
        ("DELETE", "/bookings/{id}"),
    ],
)
def test_bad_ids_in_paths(client, admin, method, path, bad_id):
    r = client.request(method, path.format(id=bad_id), json={"capacity": 3}, headers=admin)
    assert_client_error(r)


@pytest.mark.parametrize("bad_id", BAD_IDS)
def test_bad_room_ids_in_booking_body(client, user, bad_id):
    r = client.post("/bookings", json={"room_id": bad_id, "start_time": helsinki(1, 10), "end_time": helsinki(1, 11)},
                    headers=user)
    assert_client_error(r)


@pytest.mark.parametrize(
    "start, end",
    [(FAR, FAR_END), (helsinki(1, 10), FAR_END), ("0001-01-01T08:00:00+14:00", "0001-01-01T09:00:00+14:00")],
)
def test_dates_at_the_edge_of_the_calendar(client, user, room, start, end):
    r = client.post("/bookings", json={"room_id": room["id"], "start_time": start, "end_time": end}, headers=user)
    assert_client_error(r)


@pytest.mark.parametrize("day", ["9999-12-31", "0001-01-01"])
def test_availability_on_extreme_dates(client, user, room, day):
    r = client.get(f"/rooms/{room['id']}/availability", params={"date": day}, headers=user)
    assert r.status_code != 500, r.text


@pytest.mark.parametrize("path", ["/auth/register", "/bookings", "/rooms"])
def test_malformed_json(client, admin, path):
    r = client.post(path, content=b"{not json", headers={**admin, "Content-Type": "application/json"})
    assert_client_error(r)


@pytest.mark.parametrize(
    "path, body",
    [
        ("/auth/register", {"username": unique("u")}),
        ("/auth/register", {"password": "Correct-horse-42"}),
        ("/bookings", {"room_id": 1}),
        ("/bookings", {"start_time": "2026-11-02T10:00:00+02:00"}),
        ("/rooms", {"name": "No capacity"}),
    ],
)
def test_missing_fields(client, admin, path, body):
    assert_client_error(client.post(path, json=body, headers=admin))


@pytest.mark.parametrize(
    "path, body",
    [
        ("/auth/register", {"username": "u" * 10_000, "password": "Correct-horse-42"}),
        ("/auth/register", {"username": unique("u"), "password": "p" * 10_000}),
        ("/rooms", {"name": "n" * 10_000, "capacity": 2}),
        ("/rooms", {"name": unique("r"), "capacity": 2, "description": "d" * 100_000}),
    ],
)
def test_over_long_text(client, admin, path, body):
    assert_client_error(client.post(path, json=body, headers=admin))


@pytest.mark.parametrize(
    "body",
    [
        {"room_id": "one", "start_time": "2026-11-02T10:00:00+02:00", "end_time": "2026-11-02T11:00:00+02:00"},
        {"room_id": 1, "start_time": "tomorrow", "end_time": "2026-11-02T11:00:00+02:00"},
        {"room_id": 1.5, "start_time": "2026-11-02T10:00:00+02:00", "end_time": "2026-11-02T11:00:00+02:00"},
        [],
        "just a string",
    ],
)
def test_wrong_types(client, user, body):
    assert_client_error(client.post("/bookings", json=body, headers=user))


def test_login_with_missing_form_fields(client):
    assert_client_error(client.post("/auth/login", data={"username": "someone"}))
