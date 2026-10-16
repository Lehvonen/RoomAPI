# Feature Specification: Room Booking API

**Feature Branch**: `spec/sdd-init`

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "A room booking API for a small organisation's meeting rooms. Same features as our vibe-coded baseline, so the two versions can be compared: people register an account and log in; logged-in users list the active rooms, check when a room is free on a given day, book a room for a time range, see their own upcoming bookings and cancel their own bookings; admins create rooms, edit them, deactivate them, and cancel any booking. Two bookings for the same room must never overlap. Also list the stakeholders and why each one matters, and add numbered non-functional requirements (NFR-xx) for security, reliability, performance and usability next to the functional requirements (FR-xx). Every requirement needs acceptance criteria. Leave the booking rules we have not decided yet as open questions for clarify: opening hours and maximum booking length, whether bookings can be edited, and what happens to bookings when a room is deactivated."

## Stakeholders

| Stakeholder | Interest | Why they matter |
|---|---|---|
| Employee (regular user) | Find a free room and book it quickly; trust that a booking holds | The main users. Most requirements serve their booking flow. |
| Administrator (facility manager) | Keep the room list accurate; resolve conflicts by cancelling bookings | Owns the room data. A wrong room list makes every booking wrong. |
| Operator (IT) | Run the service, create the first admin account, keep data safe | Holds the only route to admin rights, and is responsible for stored passwords. |
| Client developer | Build a front end or integration on the API | Depends on a stable, documented interface and clear errors. |
| Development team and course staff | Show that the system meets its specification | The project's evidence: every requirement must be traceable to a test. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and log in (Priority: P1)

A new employee creates an account with a username and password, then logs in to get access to the system.

**Why this priority**: every other story needs an authenticated user.

**Independent Test**: register a user, log in, and call an authenticated endpoint that returns the user's own profile.

**Acceptance Scenarios**:

1. **Given** no account named "alice", **When** alice registers with a valid username and password, **Then** the account is created and the password is not returned.
2. **Given** an account "alice" exists, **When** someone registers "ALICE", **Then** registration is refused because the name is taken.
3. **Given** alice's account, **When** she logs in with the right password, **Then** she receives an access token.
4. **Given** alice's account, **When** she logs in with a wrong password or an unknown username, **Then** she is refused with the same message in both cases.

---

### User Story 2 - Book a room (Priority: P1)

A logged-in employee books an active room for a time range that does not clash with an existing booking.

**Why this priority**: booking is the core value of the system.

**Independent Test**: with one active room, book a free slot, then try to book an overlapping slot and see it refused.

**Acceptance Scenarios**:

1. **Given** an active room free from 10:00 to 11:00, **When** alice books 10:00–11:00, **Then** the booking is created and confirmed.
2. **Given** a booking for 10:00–11:00, **When** bob books 10:30–11:30 in the same room, **Then** he is refused because of the overlap.
3. **Given** a booking for 10:00–11:00, **When** bob books 11:00–12:00 in the same room, **Then** the booking is created, because back-to-back bookings do not overlap.
4. **Given** any room, **When** alice books a range whose end is not after its start, or whose start is in the past, **Then** she is refused with a message saying why.
5. **Given** two requests for the same free slot at the same moment, **When** both are processed, **Then** exactly one succeeds.

---

### User Story 3 - See rooms and availability (Priority: P2)

A logged-in employee lists the active rooms and checks when a room is booked and free on a given day.

**Why this priority**: lets users pick a free slot before booking, but booking works without it.

**Independent Test**: create rooms and bookings, then compare the room list and a day's availability with what was created.

**Acceptance Scenarios**:

1. **Given** two active rooms and one inactive room, **When** alice lists rooms, **Then** she sees only the two active rooms.
2. **Given** a room with bookings 10:00–11:00 and 13:00–14:00 on a day, **When** alice asks for that day's availability, **Then** she sees those two booked intervals and the free intervals between them.

---

### User Story 4 - See and cancel my bookings (Priority: P2)

A logged-in employee lists their own upcoming bookings and cancels one they no longer need.

**Why this priority**: users need to free rooms they will not use, but the system works without it.

**Independent Test**: book two slots, list them, cancel one, and check that the slot is free again.

**Acceptance Scenarios**:

1. **Given** alice has two upcoming bookings and bob has one, **When** alice lists her bookings, **Then** she sees only her two.
2. **Given** alice's upcoming booking, **When** she cancels it, **Then** it is marked cancelled, kept in the record, and the slot becomes bookable again.
3. **Given** alice's booking, **When** bob tries to cancel it, **Then** he is refused because he is not allowed to.

---

### User Story 5 - Manage rooms and bookings as admin (Priority: P3)

An administrator creates and edits rooms, deactivates rooms that are out of use, and cancels any booking.

**Why this priority**: needed to run the system over time, but the first rooms can be created once.

**Independent Test**: as admin, create a room, rename it, deactivate it, and cancel another user's booking; as a regular user, try the same and be refused.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they create a room with a unique name and a capacity of at least 1, **Then** the room is created and is active.
2. **Given** a room named "Aurora", **When** an admin creates or renames another room to "aurora", **Then** they are refused because the name is taken.
3. **Given** an active room, **When** an admin deactivates it, **Then** it no longer appears in room lists and cannot be booked.
4. **Given** alice's booking, **When** an admin cancels it, **Then** it is marked cancelled and records who cancelled it.
5. **Given** a regular user, **When** they try any admin action, **Then** they are refused.

---

### Edge Cases

- A time sent without a timezone offset is rejected, never guessed.
- A very large number, or a date at the edge of the calendar, in any ID or time field gets a client error, never a server error.
- A booking that has already ended cannot be cancelled by a regular user.
- Cancelling an already cancelled booking is refused.
- A cancelled booking does not block its slot.
- An expired or tampered access token is refused like a missing one.
- What happens to future bookings when their room is deactivated: see FR-009.

## Requirements *(mandatory)*

### Functional Requirements

**Accounts**

- **FR-001**: The system MUST let anyone register an account with a username and a password. Usernames are 3–50 characters from letters, digits, `_`, `.` and `-`, and are unique regardless of letter case.
  *Acceptance*: User Story 1, scenarios 1–2.
- **FR-002**: The system MUST require passwords of 10–128 characters.
  *Acceptance*: a 9-character password is refused; a 10-character password is accepted.
- **FR-003**: The system MUST let a registered user log in with username and password and receive an access token that expires after 60 minutes.
  *Acceptance*: User Story 1, scenario 3; a token older than 60 minutes is refused.
- **FR-004**: The system MUST give the same refusal for a wrong password and for an unknown username.
  *Acceptance*: User Story 1, scenario 4.
- **FR-005**: The system MUST let a logged-in user see their own profile (username, admin or not) and MUST NOT return any password data.
  *Acceptance*: the profile response has no password field.
- **FR-006**: Admin accounts MUST only be created by the operator, outside the public interface. Registration MUST always create regular users.
  *Acceptance*: a registration request that asks for admin rights creates a regular user.

**Rooms**

- **FR-007**: The system MUST let any logged-in user list active rooms with name, capacity and location, and look up a single active room.
  *Acceptance*: User Story 3, scenario 1.
- **FR-008**: The system MUST let admins create rooms (unique name regardless of case, capacity at least 1, optional location and description) and edit any of these fields.
  *Acceptance*: User Story 5, scenarios 1–2.
- **FR-009**: The system MUST let admins deactivate and reactivate a room. Inactive rooms MUST NOT be listed to regular users and MUST NOT accept new bookings. Existing future bookings of a deactivated room: [NEEDS CLARIFICATION: are they cancelled automatically, kept, or does deactivation get refused while they exist?]
  *Acceptance*: User Story 5, scenario 3.

**Availability**

- **FR-010**: The system MUST let a logged-in user see, for one active room and one calendar day, the booked intervals and the free intervals of that day.
  *Acceptance*: User Story 3, scenario 2.

**Bookings**

- **FR-011**: The system MUST let a logged-in user book an active room for a time range whose end is after its start and whose start is not in the past.
  *Acceptance*: User Story 2, scenarios 1 and 4.
- **FR-012**: Bookings MUST also respect the organisation's booking rules: [NEEDS CLARIFICATION: opening hours (if any) and the maximum length of one booking]
  *Acceptance*: to be defined with the rules.
- **FR-013**: The system MUST never accept two active bookings for the same room whose time ranges overlap. Ranges include their start and exclude their end, so back-to-back bookings are allowed. This MUST hold for simultaneous requests.
  *Acceptance*: User Story 2, scenarios 2, 3 and 5.
- **FR-014**: The system MUST let a logged-in user list their own upcoming bookings, oldest first.
  *Acceptance*: User Story 4, scenario 1.
- **FR-015**: The system MUST let users cancel their own bookings that have not ended, and let admins cancel any booking. Cancelled bookings MUST be kept with their status, the time of cancellation and who cancelled them, and MUST free their slot. Cancelling someone else's booking as a regular user MUST be refused.
  *Acceptance*: User Story 4, scenarios 2–3; User Story 5, scenario 4.
- **FR-016**: Changing an existing booking: [NEEDS CLARIFICATION: can a booking's time or room be edited, or only cancelled and booked again?]
  *Acceptance*: to be defined with the answer.

**Time**

- **FR-017**: Every time sent to the system MUST include a timezone offset; times without one MUST be rejected. Every time returned MUST be in UTC.
  *Acceptance*: `2026-10-20T09:00` is rejected; `2026-10-20T09:00+03:00` is accepted and returned as `2026-10-20T06:00Z`.

### Non-Functional Requirements

**Security**

- **NFR-001**: Passwords MUST be stored only as salted hashes from a slow, purpose-built password hashing algorithm, and MUST never be returned or written to logs.
  *Acceptance*: the stored value is not the password and differs between two users with the same password; no response or log line contains a password.
- **NFR-002**: Every operation except registration, login and a health check MUST require a valid access token.
  *Acceptance*: each protected operation refuses a missing, expired or tampered token.
- **NFR-003**: Every operation on a specific resource MUST check that the caller is allowed to act on it: their own booking, or any booking or room for admins.
  *Acceptance*: User Story 4, scenario 3; User Story 5, scenario 5.

**Reliability**

- **NFR-004**: No client input may cause a server error. Every invalid request MUST get a client error with a message that says what is wrong.
  *Acceptance*: a test set of invalid inputs (huge IDs, out-of-range dates, malformed values, missing fields) produces zero server errors.
- **NFR-005**: Overlap protection (FR-013) MUST hold when booking requests for the same slot arrive at the same time.
  *Acceptance*: User Story 2, scenario 5, run with at least 20 simultaneous requests.

**Performance**

- **NFR-006**: On a developer laptop with 1,000 bookings stored, each request MUST complete in under 500 ms.
  *Acceptance*: a timed test of every operation stays under 500 ms.

**Usability**

- **NFR-007**: The interface MUST be self-documenting: an interactive description of every operation, its inputs and its possible errors is available while the system runs.
  *Acceptance*: every operation and error response appears in the generated interface description.
- **NFR-008**: Error messages MUST be in plain English and name the field or rule that failed.
  *Acceptance*: each refusal in the acceptance scenarios carries such a message.

### Key Entities

- **User**: a person with an account. Username (unique, case-insensitive), password hash, admin flag, creation time.
- **Room**: a bookable space. Name (unique, case-insensitive), capacity, optional location and description, active flag, creation and update times.
- **Booking**: one user's claim on one room for a time range. Room, user, start, end, status (active or cancelled), creation time, cancellation time and who cancelled it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can register, log in and book a free room in under 2 minutes, using only the interactive interface description.
- **SC-002**: In a test of 20 simultaneous requests for the same free slot, exactly 1 booking is created.
- **SC-003**: 100% of functional and non-functional requirements map to at least one automated test, and all of them pass.
- **SC-004**: The invalid-input test set produces 0 server errors.
- **SC-005**: Automated tests cover at least 80% of the code.

## Assumptions

- The organisation works in one time zone, but clients always send explicit offsets (FR-017), so the system never needs to know it.
- Login attempts are not rate-limited in this version. The system runs locally for one organisation; rate limiting belongs to the network layer in front of it.
- Admins are few and trusted. There is no audit log beyond who cancelled a booking.
- Rooms are never deleted, only deactivated, so past bookings keep a valid room.
- Booking capacity (number of attendees) is not tracked; capacity is information for the user.
