# Vibe round 1: probe findings

The round-1 API (commit `75113b5`) fails 9 of 14 probe checks: 3 inputs crash the server with HTTP 500, and 6 show rules the prompt left open that the agent filled in without asking, or not at all. The 5 checks on overlap, ownership, past dates, time order and password storage hold.

Probed 2026-10-16 with [`probe.py`](probe.py), black-box through FastAPI's TestClient on a throwaway database. Raw output: [`probe-output.txt`](probe-output.txt).

| ID | Check | Result | Type | Severity |
|---|---|---|---|---|
| P4a | `GET /rooms/{id}` with id 2^70 | HTTP 500 crash | Logic (input validation) | High |
| P4b | `POST /bookings` with room_id 2^70 | HTTP 500 crash | Logic (input validation) | High |
| P5 | Booking on 9999-12-31 23:00 at UTC-5 (past year 9999 in UTC) | HTTP 500 crash | Logic (input validation) | Medium |
| P3 | Admin deactivates a room with future bookings | Bookings stay `active`, but the owner gets 404 on the room | Logic | Medium |
| P1 | One user books one room for 10 years | Accepted (no maximum length) | Logic (unspecified rule) | Medium |
| P8 | 50 wrong passwords, then the right one | All 401, then login succeeds: no lockout or delay | Security | Medium |
| P2 | Booking 03:00–04:00 | Accepted (no opening hours) | Logic (unspecified rule) | Low |
| P6 | Time sent without an offset, meant as Helsinki time | Silently stored as UTC, 3 hours off | Logic (unspecified rule) | Low |
| P7 | Register with password `aaaaaaaa` | Accepted (length is the only rule) | Security | Low |
| OK1 | Overlapping booking on the same room | Rejected, 409 | — | Holds |
| OK2 | Another user cancels someone's booking | Refused, 404 | — | Holds |
| OK3 | Booking in the past | Rejected, 422 | — | Holds |
| OK4 | End before start | Rejected, 422 | — | Holds |
| OK5 | Password storage | Salted PBKDF2-SHA256, not plain text | — | Holds |

Severity is the probe author's judgment: High = any user can crash a request with one call; Medium = wrong data or abuse possible; Low = surprising but documented or minor.
