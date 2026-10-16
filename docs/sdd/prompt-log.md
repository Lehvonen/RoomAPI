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

<!-- Copy a block above for each new prompt. -->
