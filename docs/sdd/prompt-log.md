# SDD prompt log

Source material for report §4.3 (deriving requirements) and §4.5 (prompts).
Log every prompt given to Spec Kit or the coding agent, in order. Paste the prompt verbatim.

## Prompts

### 1. Constitution (`/speckit-constitution`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated #12. The prompt was AI-drafted and approved by Ivar Lehvonen on 2026-10-16. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `597fdf0` |
| Purpose | Fix the project's non-negotiable rules before any spec exists. |
| Reasoning for the wording | Each principle answers a failure seen in the vibe version: unstated rules filled in by the agent (→ I), tests written after the code (→ II), HTTP 500 on bad input (→ III), times silently read as UTC (→ IV). Stack and workflow are stated so the plan can't drift from them. |
| Expected result | Five principles with MUST rules and rationale, plus constraints, workflow and governance; version 1.0.0. |
| What came back | Constitution v1.0.0 with five principles (Specification First, Test-First, Secure by Default, Explicit Time Handling, Simplicity), Technical Constraints, Development Workflow and Governance. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | None found. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | None needed. |

Prompt (verbatim):

```text
/speckit-constitution RoomAPI is a room booking REST API for a small organisation. Principles:

1. Specification first: every behaviour comes from a numbered requirement (FR-xx, NFR-xx) with acceptance criteria. Nothing is built that the spec doesn't state, and open questions are settled with clarify before planning.
2. Test-first: pytest tests are written from the acceptance criteria and committed before the implementation. Every FR and NFR maps to at least one test.
3. Secure by default: passwords hashed with bcrypt or Argon2, never stored or logged in plain text. Every endpoint except register, login and health requires a valid token and checks authorization. Invalid input returns a 4xx error, never a 500.
4. Explicit time handling: all times are stored and returned in UTC. Input times must carry a timezone offset; times without one are rejected.
5. Simplicity: FastAPI, SQLite via SQLAlchemy, Pydantic and pytest; no other services.

Constraints: Python 3.11 or newer, managed with uv. Runs locally; nothing is deployed.

Workflow: every change goes through a pull request linked to an issue, reviewed and merged by the other team member. CI runs pytest with coverage on every pull request. Commit messages follow CONTRIBUTING.md (type(ref): description).
```

### 2. Specify (`/speckit-specify`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated #12. The prompt was AI-drafted and approved by Ivar Lehvonen on 2026-10-16. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `fdbbf6a` (draft), `f839e6f` (open questions answered) |
| Purpose | Turn the vibe prompt's feature list into numbered, testable requirements. |
| Reasoning for the wording | Same features as the vibe round-1 prompt, so the comparison is fair. Stakeholders and NFRs are asked for explicitly, because Spec Kit's template has neither and report §2.1 and §2.3 need both. The undecided booking rules are named as open questions, so a person decides them instead of the agent. |
| Expected result | A spec with stakeholders, user stories, FR-xx, NFR-xx and acceptance criteria, and exactly the named rules left as [NEEDS CLARIFICATION]. |
| What came back | 5 stakeholders, 5 prioritised user stories, FR-001–FR-017, NFR-001–NFR-008, 5 success criteria, and 3 open questions (FR-009, FR-012, FR-016). Quality checklist 14/16 until those were answered. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | None in the output. The 3 open questions were answered by Ivar Lehvonen: opening hours 08:00–18:00 Helsinki time with a 4-hour maximum; deactivation refused while future bookings exist; bookings cancelled and rebooked, never edited. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | None needed. |

Prompt (verbatim):

```text
/speckit-specify A room booking API for a small organisation's meeting rooms. Same features as our vibe-coded baseline, so the two versions can be compared:

- People register an account and log in.
- Logged-in users list the active rooms, check when a room is free on a given day, book a room for a time range, see their own upcoming bookings and cancel their own bookings.
- Admins create rooms, edit them, deactivate them, and cancel any booking.

Two bookings for the same room must never overlap.

Also list the stakeholders and why each one matters, and add numbered non-functional requirements (NFR-xx) for security, reliability, performance and usability next to the functional requirements (FR-xx). Every requirement needs acceptance criteria.

Leave the booking rules we have not decided yet as open questions for clarify: opening hours and maximum booking length, whether bookings can be edited, and what happens to bookings when a room is deactivated.
```

### 3. Clarify (`/speckit-clarify`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated #12. The prompt was AI-drafted and approved by Ivar Lehvonen on 2026-10-16. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `92d1e7b` |
| Purpose | Find ambiguities the spec still had, before planning. |
| Reasoning for the wording | Points the scan at the areas where the vibe version failed: login abuse, tokens, input limits. Also at availability, which became ambiguous once opening hours existed. |
| Expected result | Up to 5 questions with a recommended answer, each answer written back into the spec. |
| What came back | 4 questions, all answered by Ivar Lehvonen with the recommended option: slow down repeated failed logins but never lock (new NFR-009); bookings at most 90 days ahead (FR-011); availability covers the Helsinki date's opening hours (FR-010); no logout (FR-003). Checklist 16/16. |
| Met expectations? | Yes. It also exposed a conflict: NFR-006's 500 ms limit against NFR-009's deliberate 2-second delay. The conflict was fixed in the spec before planning (`3016b16`). |
| Issues (incorrect, incomplete or inefficient output) | The skill asks one question at a time; the 4 were asked together, to save a round trip. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | None needed. |

Prompt (verbatim):

```text
/speckit-clarify Check the spec for anything still ambiguous, with extra attention to security and reliability (login abuse, tokens, input limits) and to the availability rules now that opening hours exist.
```

### 4. Plan (`/speckit-plan`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated #12. The prompt was AI-drafted and approved by Ivar Lehvonen on 2026-10-16. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `17a5fd1` |
| Purpose | Fix the technical design: stack, data model, API contract, test approach. |
| Reasoning for the wording | Names each library, so the plan has no open technology choices. Asks for black-box tests with a configurable base URL, so the same suite can run against vibe in Phase 5. |
| Expected result | plan.md passing the Constitution Check, research.md with decisions, data-model.md, an API contract and quickstart.md. |
| What came back | All five artifacts. Research decisions R1–R8: BEGIN IMMEDIATE for overlaps; Argon2id; JWT; AwareDatetime and Helsinki opening hours; explicit input bounds; the login slow-down table; dual-mode test client; the uv project. The contract maps each endpoint to its FR/NFR and lists the endpoint differences from vibe. The Constitution Check passes before and after design. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | None found. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | None needed. |

Prompt (verbatim):

```text
/speckit-plan Use the constitution's stack: Python 3.11+, FastAPI, SQLite via SQLAlchemy 2, Pydantic v2, pytest, with uv managing the project in sdd/. Hash passwords with Argon2 (argon2-cffi) and issue JWT access tokens (PyJWT). Use zoneinfo with the tzdata package for Europe/Helsinki opening hours. Write the acceptance tests as black-box HTTP tests with a configurable base URL, so the same suite can later be run against the vibe-coded version for the comparison. Keep the code small: one app package with routers for auth, rooms and bookings.
```

### 5. Tasks (`/speckit-tasks`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | Claude Code, on behalf of Ivar Lehvonen, who delegated #12. The prompt was AI-drafted and approved by Ivar Lehvonen on 2026-10-16. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `23ee4cd`, issues linked in `7a12d8c` |
| Purpose | Break the plan into ordered, test-first tasks that map onto GitHub issues. |
| Reasoning for the wording | Restates Test-First because Spec Kit treats tests as optional. Asks for issue-sized groups so the work becomes visible in GitHub. |
| Expected result | tasks.md with tests before implementation in every story, and a handful of issue groups. |
| What came back | 37 tasks in 8 phases, in 6 issue groups (A–F), created as issues #16–#21. Every story's tests come before its implementation. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | None found. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | None needed. |

Prompt (verbatim):

```text
/speckit-tasks Tests first: for each user story, the acceptance tests come before the implementation tasks. Size the tasks so each one fits a small pull request, and group them so the work can be split into a handful of GitHub issues.
```

### 6. Implement, group A (`/speckit-implement`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | AI-drafted; reviewed and approved by Ivar Lehvonen after the run (2026-10-16). |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `3169baa` (setup), `9fa2bd1`–`61b71d7` (foundation), `6a2ef7c` (tasks marked done) |
| Purpose | Build the project setup and foundation (issue #16, tasks T001–T013) without starting any user story. |
| Reasoning for the wording | Limits the run to one issue group, so the work lands as one reviewable pull request and the stories stay test-first in their own pull requests. |
| Expected result | uv project, CI, config, database, models, time rules, security, schemas, app factory, admin CLI and test harness; T001–T013 marked done. |
| What came back | All 13 tasks done. The health smoke test passes; coverage is 40%, as expected with no story tests yet. A manual check of the time rules: 08:00–12:00 accepted; 07:30–08:30, 17:00–18:30, 09:00–13:30 and an overnight booking refused; a year-9999 start refused by the 90-day rule instead of overflowing; the opening window follows the 2026-10-25 change to winter time. |
| Met expectations? | Yes, after two corrections to the task list. |
| Issues (incorrect, incomplete or inefficient output) | (1) T004's 80% coverage gate would have failed CI on every pull request until group F, and pytest fails when it finds no tests at all. The gate moved to T035, and T013 gained a health smoke test (`50f5b2d`), before any code was written. (2) Starlette's test client warned that it now expects `httpx2`, which was added as a dev dependency and recorded in research R8. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | No prompt change. The task list was corrected instead, so CI can pass from the first pull request, as the constitution requires. |

Prompt (verbatim):

```text
/speckit-implement Only issue group A (#16): tasks T001–T013, project setup and foundation. Stop after T013 and mark only those tasks done.
```

### 7. Implement, group B (`/speckit-implement`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | AI-drafted, edited and approved by Ivar Lehvonen before the run. His edit: "Stop after T016" became "Do not continue after T016". |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `834d9fd` (failing tests), `5da5fa6` (implementation), `813c26b` (tasks marked done) |
| Purpose | Build User Story 1, register and log in (issue #17, tasks T014–T016), test-first. |
| Reasoning for the wording | Spells out the test-first order (write, run, commit while failing, then implement) so the history proves Constitution II. Adds the failed-login tidy-up from the #23 review, so the NFR-009 table is clean before the slow-down is built. |
| Expected result | Failing US1 tests in their own commit, then registration, login and profile until they pass. |
| What came back | 23 US1 tests, committed while failing (21 failed, 2 errors, because the endpoints didn't exist). After implementation, all 24 tests pass (23 plus health). Coverage rose from 40% to 74%; `routers/auth.py` is at 100%. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | None found. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | Ivar's wording edit only; no rerun needed. |

Prompt (verbatim):

```text
/speckit-implement Only issue group B (#17): tasks T014–T016, User Story 1 (register and log in). Test-first: write T014's acceptance tests, run them and commit them while they fail, then implement T015 and T016 until they pass. Also lower-case and limit to 50 characters the username stored in failed_logins. Do not continue after T016 and mark only those tasks done.
```

### 8. Implement, group C (`/speckit-implement`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | AI-drafted, edited and approved by Ivar Lehvonen before the run. He held back the first draft and sent his own wording. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `337f881` (failing tests), `75824b9` (implementation), `77f7dce` (mutation-check evidence), `b566b7d` (tasks marked done) |
| Purpose | Build User Story 2, booking a room (issue #18, tasks T017–T020), test-first. |
| Reasoning for the wording | Names all three test tasks and their order before the implementation. States the one rule the #23 review flagged: a broken booking rule must give 422 with its message, never 500. |
| Expected result | Failing booking, concurrency and time-rule tests committed first; then `POST /bookings` until they pass. |
| What came back | 24 acceptance tests (US2 and the 20-request concurrency test), committed while all 24 failed, and 19 time-rule unit tests. After implementation, all 68 tests pass. Coverage rose from 74% to 92%; `routers/bookings.py` is at 100%. A mutation check removed the `BEGIN IMMEDIATE` lock: the concurrency test then failed with 10, 5 and 7 double bookings in three runs, so it really catches the race ([evidence](../evidence/sdd/concurrency-mutation-check.md)). |
| Met expectations? | Yes, with three deviations, listed under Issues. |
| Issues (incorrect, incomplete or inefficient output) | (1) The 19 time-rule unit tests already passed when committed, because `timerules.py` was built in the foundation (the deviation recorded in the plan's Complexity Tracking). (2) Two "room not found" tests first passed for the wrong reason: with no `/bookings` route, FastAPI also answers 404. They now also check the message, so they failed until the endpoint existed. (3) T017's "a cancelled booking doesn't block its slot" needs the cancel endpoint, so it moves to US4's tests (T024, scenario 2). Creating rooms is US5, so tests set rooms up through the harness: directly in the test database in-process, or through the admin API against another server. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | Ivar's rewrite was used as is; no rerun needed. |

Prompt (verbatim):

```text
/speckit-implement Issue group C only (#18) : tasks T017–T020, User Story 2 (book a room). Write the acceptance tests (T017) first and the 20-request concurrency test (T018) and the time-rule unit tests (T019). Run them and commit them while they fail, then implement T020 until they pass. Booking-rule errors must come back as 422 with their message, never as 500. Do not continue after T020 and mark only those tasks done.
```

### 9. Implement, group D (`/speckit-implement`)

| Field | Entry |
|---|---|
| Date | 2026-10-16 |
| Who prompted | AI-drafted, edited and approved by Ivar Lehvonen before the run. He held back the first draft and sent his own wording. |
| Tool / model | Spec Kit 1.1.4.dev0 with the Claude Code integration, run by Claude Code (`claude-opus-5-5`) |
| Commit | `d41b8f7` (failing tests), `87a547d` (rooms and availability), `33dba83` (my bookings and cancel), `8226628` (tasks marked done) |
| Purpose | Build User Stories 3 and 4 (issue #19, tasks T021–T026), test-first. |
| Reasoning for the wording | Names both stories and their test tasks first. Explicitly includes "a cancelled booking frees its slot", which moved here from US2 because this group builds cancelling. |
| Expected result | Failing US3 and US4 tests committed first; then room list, room lookup, availability, my bookings and cancel until they pass. |
| What came back | 31 acceptance tests, committed while all 31 failed. After implementation, all 100 tests pass. Coverage rose from 92% to 93%; all three routers are at 100%. The cancel test checks that the freed slot can be booked again and that availability shows only the new booking. |
| Met expectations? | Yes. |
| Issues (incorrect, incomplete or inefficient output) | Two availability 404 tests first passed only because the route didn't exist yet: FastAPI answers 404 for a missing route too. This repeated #18's finding. They now also check the message, so they failed until the endpoint existed. Ended bookings can't be created through the API (FR-011), so in-process tests insert them directly for the "ended" cases. |
| Refinement, why it was needed, and how the revised prompt improved the outcome | Ivar's rewrite was used as is; no rerun needed. |

Prompt (verbatim):

```text
/speckit-implement Only group D issue (#19): tasks T021–T026, User Story 3 (see rooms and availability) and User Story 4 (see and cancel my bookings). Start with writing the acceptance tests T021 and T024, including that a cancelled booking frees its slot. Run & commit while they fail, after that implement T022, T023, T025 and T026 until they pass. Do not continue after T026 and mark only those tasks done.
```

<!-- Copy a block above for each new prompt. -->
