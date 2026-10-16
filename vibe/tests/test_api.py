from datetime import datetime, timedelta, timezone

from .conftest import HELSINKI, PASSWORD, slot


# --- auth ---------------------------------------------------------------

def test_register_login_and_me(client, user):
    r = client.get("/users/me", headers=user)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"
    assert r.json()["is_admin"] is False


def test_duplicate_username_rejected_case_insensitive(client, user):
    r = client.post("/auth/register", json={"username": "ALICE", "password": PASSWORD})
    assert r.status_code == 409


def test_register_validation(client):
    assert client.post("/auth/register", json={"username": "ab", "password": PASSWORD}).status_code == 422
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
    start, end = slot(9)  # 09:00-10:00 Finnish time
    assert book(client, user, room["id"], start, end).status_code == 201
    # The same instant + 30 min, written with a +02:00 offset -> overlaps
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
    hour = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(HELSINKI).hour
    hours = lambda slots: [(hour(s["start"]), hour(s["end"])) for s in slots]
    assert hours(data["booked"]) == [(9, 10), (13, 15)]
    # Free slots only cover opening hours (07:00-20:00)
    assert hours(data["free"]) == [(7, 9), (10, 13), (15, 20)]


def test_availability_default_window_and_validation(client, user, room):
    assert client.get(f"/rooms/{room['id']}/availability", headers=user).status_code == 200
    start, end = slot(9)
    r = client.get(f"/rooms/{room['id']}/availability", params={"start": end, "end": start}, headers=user)
    assert r.status_code == 422


def test_cli_promotes_existing_user(client, db_file, user):
    from app.cli import create_admin

    create_admin(db_file, "alice", None)
    assert client.get("/users/me", headers=user).json()["is_admin"] is True


# --- regression tests for reported problems ------------------------------

HUGE = 2**70


def test_huge_ids_are_rejected_not_500(client, admin, user, room):
    for path in (f"/rooms/{HUGE}", f"/rooms/{HUGE}/availability", f"/bookings/{HUGE}"):
        assert client.get(path, headers=user).status_code == 422, path
    assert client.delete(f"/bookings/{HUGE}", headers=user).status_code == 422
    assert client.patch(f"/rooms/{HUGE}", json={"capacity": 2}, headers=admin).status_code == 422
    assert client.get("/bookings", params={"room_id": HUGE}, headers=user).status_code == 422
    assert client.get("/rooms", params={"min_capacity": HUGE}, headers=user).status_code == 422
    assert book(client, user, HUGE, *slot(9)).status_code == 422
    # The largest SQLite integer is still a valid (missing) ID
    assert client.get(f"/rooms/{2**63 - 1}", headers=user).status_code == 404


def test_extreme_dates_are_rejected_not_500(client, user, room):
    for start, end in [
        ("9999-12-31T23:00:00", "9999-12-31T23:59:59"),
        ("9999-12-31T22:00:00-02:00", "9999-12-31T23:00:00-02:00"),
        ("9999-12-31T23:00:00+00:00", "9999-12-31T23:59:59+00:00"),
    ]:
        r = book(client, user, room["id"], start, end)
        assert r.status_code == 422, (start, r.text)
    # Inside opening hours on the last representable day is fine
    assert book(client, user, room["id"], "9999-12-31T09:00:00", "9999-12-31T10:00:00").status_code == 201
    for params in (
        {"start": "9999-12-31T23:00:00+00:00"},
        {"start": "9999-12-31T00:00:00", "end": "9999-12-31T23:59:59+00:00"},
        {"start": "0001-01-01T00:00:00"},
    ):
        r = client.get(f"/rooms/{room['id']}/availability", params=params, headers=user)
        assert r.status_code == 422, (params, r.text)


def test_deactivating_room_cancels_its_upcoming_bookings(client, admin, user, room):
    b = book(client, user, room["id"], *slot(9)).json()
    assert client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin).status_code == 200
    r = client.get(f"/bookings/{b['id']}", headers=user).json()
    assert r["status"] == "cancelled"
    assert client.get("/bookings", headers=user).json() == []
    # Reactivating does not bring old bookings back, but the room can be booked again
    client.patch(f"/rooms/{room['id']}", json={"is_active": True}, headers=admin)
    assert client.get(f"/bookings/{b['id']}", headers=user).json()["status"] == "cancelled"
    assert book(client, user, room["id"], *slot(9)).status_code == 201


def test_other_room_edits_keep_bookings(client, admin, user, room):
    b = book(client, user, room["id"], *slot(9)).json()
    client.patch(f"/rooms/{room['id']}", json={"capacity": 3}, headers=admin)
    assert client.get(f"/bookings/{b['id']}", headers=user).json()["status"] == "active"


def test_max_booking_length(client, user, room):
    assert book(client, user, room["id"], *slot(8, 8)).status_code == 201
    r = book(client, user, room["id"], *slot(7, 9))
    assert r.status_code == 422
    start, _ = slot(9)
    ten_years = (datetime.fromisoformat(start) + timedelta(days=3650)).isoformat()
    assert book(client, user, room["id"], start, ten_years).status_code == 422


def test_opening_hours(client, user, room):
    assert book(client, user, room["id"], *slot(7)).status_code == 201       # 07-08 ok
    assert book(client, user, room["id"], *slot(19)).status_code == 201      # 19-20 ok
    assert book(client, user, room["id"], *slot(6.5)).status_code == 422     # starts 06:30
    assert book(client, user, room["id"], *slot(19.5)).status_code == 422    # ends 20:30
    assert book(client, user, room["id"], *slot(2)).status_code == 422       # middle of the night
    assert book(client, user, room["id"], *slot(18, 16)).status_code == 422  # overnight


def test_times_without_offset_are_finnish_time(client, user, room):
    day = (datetime.now(HELSINKI) + timedelta(days=1)).date()
    r = book(client, user, room["id"], f"{day}T10:00:00", f"{day}T11:00:00")
    assert r.status_code == 201, r.text
    start = datetime.fromisoformat(r.json()["start_time"])
    assert start == datetime(day.year, day.month, day.day, 10, tzinfo=HELSINKI)
    assert start.astimezone(HELSINKI).hour == 10
    # Responses are given in Finnish time
    assert start.utcoffset() == HELSINKI.utcoffset(start.replace(tzinfo=None))


def test_weak_passwords_rejected(client):
    for pw in ("aaaaaaaa", "aaaaaaaaaaaa", "abcdefghijkl", "1234567890", "a1a1a1a1a1a1", "password123", "carol-1234567"):
        r = client.post("/auth/register", json={"username": "carol", "password": pw})
        assert r.status_code == 422, pw
    assert client.post("/auth/register", json={"username": "carol", "password": "Tuli-ja-jaa7"}).status_code == 201


def test_cli_rejects_weak_admin_password(db_file):
    from app.cli import main

    assert main(["create-admin", "boss", "--password", "aaaaaaaa", "--db", db_file]) == 1


def test_login_lockout_after_repeated_failures(client, user):
    for _ in range(5):
        assert client.post("/auth/login", data={"username": "alice", "password": "wrong-pass1"}).status_code == 401
    r = client.post("/auth/login", data={"username": "alice", "password": PASSWORD})
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    # Usernames are case-insensitive, so the lock cannot be dodged with ALICE
    assert client.post("/auth/login", data={"username": "ALICE", "password": PASSWORD}).status_code == 429


def test_successful_login_resets_failure_count(client, user):
    for _ in range(4):
        client.post("/auth/login", data={"username": "alice", "password": "wrong-pass1"})
    assert client.post("/auth/login", data={"username": "alice", "password": PASSWORD}).status_code == 200
    for _ in range(4):
        client.post("/auth/login", data={"username": "alice", "password": "wrong-pass1"})
    assert client.post("/auth/login", data={"username": "alice", "password": PASSWORD}).status_code == 200


def test_login_lockout_per_ip_across_usernames(client, user):
    for i in range(20):
        client.post("/auth/login", data={"username": f"ghost{i}", "password": "wrong-pass1"})
    assert client.post("/auth/login", data={"username": "alice", "password": PASSWORD}).status_code == 429
