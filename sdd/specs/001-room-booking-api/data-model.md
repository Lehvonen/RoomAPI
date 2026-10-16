# Data Model: Room Booking API

Four tables in one SQLite file. All times are stored in UTC (constitution IV). Names follow the spec's Key Entities.

## User (`users`)

| Field | Type | Rules | Source |
|---|---|---|---|
| id | integer, primary key | 1 … 2^63−1 | |
| username | text, unique, case-insensitive | 3–50 characters from `A–Z a–z 0–9 _ . -` | FR-001 |
| password_hash | text | Argon2id hash; never returned or logged | NFR-001 |
| is_admin | boolean, default false | set only by the operator CLI | FR-006 |
| created_at | UTC datetime | | |

The plain password (10–128 characters, FR-002) is checked on registration and never stored.

## Room (`rooms`)

| Field | Type | Rules | Source |
|---|---|---|---|
| id | integer, primary key | 1 … 2^63−1 | |
| name | text, unique, case-insensitive | 1–100 characters | FR-008 |
| capacity | integer | 1 … 10,000 | FR-008 |
| location | text, optional | up to 200 characters | FR-008 |
| description | text, optional | up to 2,000 characters | FR-008 |
| is_active | boolean, default true | | FR-009 |
| created_at, updated_at | UTC datetime | | |

**State**: `active ⇄ inactive`. The change to inactive is refused while the room has active bookings that have not ended (FR-009).

## Booking (`bookings`)

| Field | Type | Rules | Source |
|---|---|---|---|
| id | integer, primary key | 1 … 2^63−1 | |
| room_id | foreign key → rooms | room must be active when booked | FR-011 |
| user_id | foreign key → users | the booker | |
| start_time, end_time | UTC datetime | end > start; start ≥ now and ≤ now + 90 days; both inside 08:00–18:00 on the same Helsinki date; length ≤ 4 h | FR-011, FR-012 |
| status | `active` or `cancelled` | | FR-015 |
| created_at | UTC datetime | | |
| cancelled_at | UTC datetime, optional | set on cancellation | FR-015 |
| cancelled_by | foreign key → users, optional | set on cancellation | FR-015 |

**Constraints**: `CHECK (end_time > start_time)`. There is no overlap constraint in the schema; overlaps are prevented inside a `BEGIN IMMEDIATE` transaction ([research R1](research.md)). Index on `(room_id, status, start_time, end_time)`.

**State**: `active → cancelled`, never back. The owner may cancel before `end_time`; an admin may cancel at any time. Bookings are never edited (FR-016) or deleted.

## Failed login (`failed_logins`)

| Field | Type | Rules | Source |
|---|---|---|---|
| id | integer, primary key | | |
| username | text | lower-cased as entered, whether or not the user exists | NFR-009 |
| attempted_at | UTC datetime | rows older than 15 minutes may be deleted | NFR-009 |

Five or more rows for a username within 15 minutes trigger the 2-second delay. A successful login deletes that username's rows.
