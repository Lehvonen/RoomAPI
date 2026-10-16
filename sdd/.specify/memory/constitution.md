# RoomAPI Constitution

## Core Principles

### I. Specification First

Every behaviour of the system MUST trace back to a numbered requirement in the feature spec:
functional requirements as `FR-xx`, non-functional requirements as `NFR-xx`, each with testable
acceptance criteria.

- Behaviour that no requirement states MUST NOT be implemented.
- Ambiguities MUST be settled through `/speckit-clarify` and recorded in the spec before planning.
- When code and spec disagree, the spec is corrected first, through a reviewed change, and then the code.

Rationale: the vibe-coded baseline showed an agent filling unstated rules with its own defaults.
Here every rule is decided and written down before code exists.

### II. Test-First (NON-NEGOTIABLE)

- pytest tests MUST be written from the acceptance criteria and committed before the implementation
  they cover.
- A test MUST fail before its implementation lands, and pass after.
- Every `FR-xx` and `NFR-xx` MUST map to at least one test, recorded in a traceability table.

Rationale: tests derived from the spec are the evidence that the generated code implements it.

### III. Secure by Default

- Passwords MUST be hashed with bcrypt or Argon2, and MUST NOT be stored, returned or logged in
  plain text.
- Every endpoint except register, login and health MUST require a valid token and MUST check that
  the caller is authorized for the specific resource.
- Invalid input MUST be answered with a 4xx status and a clear message. An unhandled error (HTTP 500)
  on any client input is a defect.

Rationale: authentication, authorization and input validation are where generated code most often
fails silently.

### IV. Explicit Time Handling

- All times MUST be stored and returned in UTC.
- Input times MUST carry a timezone offset. Times without one MUST be rejected with a 4xx error,
  never interpreted.

Rationale: a guessed time zone produces bookings at the wrong hour with no error at all.

### V. Simplicity

- The stack is FastAPI, SQLite via SQLAlchemy, Pydantic and pytest. Other services, frameworks or
  infrastructure MUST NOT be added.
- Features beyond the spec MUST NOT be added.

Rationale: a small, fixed stack keeps the specification, not the tooling, at the centre of the
project.

## Technical Constraints

- Python 3.11 or newer, with dependencies managed by uv.
- The system runs locally. SQLite is a file that is not committed, and tests use a fresh database.
- Nothing is deployed. CI runs on GitHub Actions.

## Development Workflow

- Every change goes through a pull request linked to an issue. Direct pushes to `main` are not
  allowed.
- Each pull request is reviewed and merged by the team member who did not author it.
- CI MUST run pytest with coverage on every pull request, and MUST pass before merge.
- Commit messages MUST follow `CONTRIBUTING.md`: `type(ref): description`, where `ref` is a
  requirement ID, a report section, or a prompt round.
- Every prompt given to Spec Kit or the coding agent is logged verbatim in `docs/sdd/prompt-log.md`,
  in the same pull request as its output.

## Governance

This constitution overrides any other practice in the `sdd/` project.

- Amendments are made through a pull request that states what changes and why, and are approved by
  both team members.
- Versioning follows semantic versioning: MAJOR for removing or redefining a principle, MINOR for a
  new principle or section, PATCH for wording.
- Every pull request review checks compliance with these principles. A deviation MUST be justified
  in the pull request and recorded in the plan's complexity tracking.

**Version**: 1.0.0 | **Ratified**: 2026-10-16 | **Last Amended**: 2026-10-16
