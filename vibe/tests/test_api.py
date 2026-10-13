from datetime import datetime, timedelta, timezone

from .conftest import slot


# --- auth ---------------------------------------------------------------

def test_register_login_and_me(client, user):
    r = client.get("/users/me", headers=user)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"
    assert r.json()["is_admin"] is False


def test_duplicate_username_rejected_case_insensitive(client, user):
    r = client.post("/auth/register", json={"username": "ALICE", "password": "password123"})
    assert r.status_code == 409


def test_register_validation(client):
    assert client.post("/auth/register", json={"username": "ab", "password": "password123"}).status_code == 422
    assert client.post("/auth/register", json={"username": "carol", "password": "short"}).status_code == 422


def test_wrong_password_and_unknown_user(client, user):
    assert client.post("/auth/login", data={"username": "alice", "password": "nope-nope"}).status_code == 401
    assert client.post("/auth/login", data={"username": "ghost", "password": "nope-nope"}).status_code == 401


def test_endpoints_require_auth(client):
    assert client.get("/rooms").status_code == 401
    assert client.get("/bookings").status_code == 401
    assert client.get("/rooms", headers={"Authorization": "Bearer garbage"}).status_code == 401


# --- rooms --------------------------------------------------------------

def test_admin_creates_and_edits_room(client, admin, user, room):
    r = client.patch(f"/rooms/{room['id']}", json={"capacity": 12, "description": "Has a projector"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["capacity"] == 12
    assert r.json()["name"] == "Aurora"

    rooms = client.get("/rooms", headers=user).json()
    assert [x["name"] for x in rooms] == ["Aurora"]


def test_regular_user_cannot_manage_rooms(client, user, room):
    assert client.post("/rooms", json={"name": "X", "capacity": 2}, headers=user).status_code == 403
    assert client.patch(f"/rooms/{room['id']}", json={"capacity": 1}, headers=user).status_code == 403


def test_duplicate_room_name(client, admin, room):
    assert client.post("/rooms", json={"name": "aurora", "capacity": 3}, headers=admin).status_code == 409


def test_patch_rejects_null_name(client, admin, room):
    assert client.patch(f"/rooms/{room['id']}", json={"name": None}, headers=admin).status_code == 422


def test_inactive_rooms_hidden_from_users(client, admin, user, room):
    client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin)
    assert client.get("/rooms", headers=user).json() == []
    assert client.get(f"/rooms/{room['id']}", headers=user).status_code == 404
    assert len(client.get("/rooms?include_inactive=true", headers=admin).json()) == 1
    start, end = slot(10)
    r = client.post("/bookings", json={"room_id": room["id"], "start_time": start, "end_time": end}, headers=user)
    assert r.status_code == 404


# --- bookings -----------------------------------------------------------

def book(client, headers, room_id, start, end):
    return client.post("/bookings", json={"room_id": room_id, "start_time": start, "end_time": end}, headers=headers)


def test_book_and_list_own(client, user, other_user, room):
    start, end = slot(9)
    r = book(client, user, room["id"], start, end)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "active"
    assert r.json()["room_name"] == "Aurora"

    assert len(client.get("/bookings", headers=user).json()) == 1
    assert client.get("/bookings", headers=other_user).json() == []


def test_overlapping_booking_rejected(client, user, other_user, room):
    start, end = slot(9, 2)  # 09-11
    assert book(client, user, room["id"], start, end).status_code == 201
    s2, e2 = slot(10)  # 10-11 overlaps
    assert book(client, other_user, room["id"], s2, e2).status_code == 409
    s3, e3 = slot(8, 4)  # 08-12 contains it
    assert book(client, other_user, room["id"], s3, e3).status_code == 409


def test_back_to_back_bookings_allowed(client, user, room):
    s1, e1 = slot(9)
    s2, e2 = slot(10)
    assert book(client, user, room["id"], s1, e1).status_code == 201
    assert book(client, user, room["id"], s2, e2).status_code == 201


def test_timezone_offsets_are_compared_correctly(client, user, other_user, room):
    start, end = slot(9)  # 09:00-10:00 UTC
    assert book(client, user, room["id"], start, end).status_code == 201
    # 11:30+02:00 == 09:30 UTC -> overlaps
    s = datetime.fromisoformat(start).astimezone(timezone(timedelta(hours=2))) + timedelta(minutes=30)
    r = book(client, other_user, room["id"], s.isoformat(), (s + timedelta(hours=1)).isoformat())
    assert r.status_code == 409


def test_invalid_times(client, user, room):
    start, end = slot(9)
    assert book(client, user, room["id"], end, start).status_code == 422
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    r = book(client, user, room["id"], past.isoformat(), (past + timedelta(hours=1)).isoformat())
    assert r.status_code == 422
    assert book(client, user, 9999, start, end).status_code == 404


def test_cancel_own_booking_frees_slot(client, user, other_user, room):
    start, end = slot(9)
    booking = book(client, user, room["id"], start, end).json()
    assert client.delete(f"/bookings/{booking['id']}", headers=user).status_code == 204
    assert client.delete(f"/bookings/{booking['id']}", headers=user).status_code == 409
    assert client.get("/bookings", headers=user).json() == []
    assert client.get("/bookings?include_cancelled=true", headers=user).json()[0]["status"] == "cancelled"
    assert book(client, other_user, room["id"], start, end).status_code == 201


def test_cannot_see_or_cancel_others_booking(client, user, other_user, room):
    start, end = slot(9)
    booking = book(client, user, room["id"], start, end).json()
    assert client.get(f"/bookings/{booking['id']}", headers=other_user).status_code == 404
    assert client.delete(f"/bookings/{booking['id']}", headers=other_user).status_code == 404


def test_admin_can_list_and_cancel_any_booking(client, admin, user, other_user, room):
    s1, e1 = slot(9)
    s2, e2 = slot(11)
    b1 = book(client, user, room["id"], s1, e1).json()
    book(client, other_user, room["id"], s2, e2)
    assert client.get("/bookings?all_users=true", headers=user).status_code == 403
    assert len(client.get("/bookings?all_users=true", headers=admin).json()) == 2
    assert client.delete(f"/bookings/{b1['id']}", headers=admin).status_code == 204


def test_availability(client, user, room):
    book(client, user, room["id"], *slot(9))
    book(client, user, room["id"], *slot(13, 2))
    day_start, _ = slot(0)
    _, day_end = slot(23)
    r = client.get(f"/rooms/{room['id']}/availability", params={"start": day_start, "end": day_end}, headers=user)
    assert r.status_code == 200
    data = r.json()
    hour = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")).hour  # py3.10 can't parse "Z"
    hours = lambda slots: [(hour(s["start"]), hour(s["end"])) for s in slots]
    assert hours(data["booked"]) == [(9, 10), (13, 15)]
    assert hours(data["free"]) == [(0, 9), (10, 13), (15, 0)]


def test_availability_default_window_and_validation(client, user, room):
    assert client.get(f"/rooms/{room['id']}/availability", headers=user).status_code == 200
    start, end = slot(9)
    r = client.get(f"/rooms/{room['id']}/availability", params={"start": end, "end": start}, headers=user)
    assert r.status_code == 422


def test_cli_promotes_existing_user(client, db_file, user):
    from app.cli import create_admin

    create_admin(db_file, "alice", None)
    assert client.get("/users/me", headers=user).json()["is_admin"] is True
