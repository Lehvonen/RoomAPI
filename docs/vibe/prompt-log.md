# Vibe coding prompt log

Source material for report §3.2 (master prompts) and §3.3 (prompt iteration log).
Each round's raw agent output is kept verbatim in its own file (`round-N-output.md`).

Fill every `TODO` from what you actually did and saw. Nothing here should be reconstructed after the fact.

## §3.2 Prompts

### Round 1

| Field | Entry |
|---|---|
| Date | 2026-10-13 |
| Tool / model | Claude Code (TODO: model name) |
| Commit | `vibe(round-1): room booking API from first prompt (FastAPI + SQLite)` |
| Raw output | [`round-1-output.md`](round-1-output.md) |
| Purpose | TODO |
| Reasoning for the wording | TODO |
| Expected result | TODO |
| What came back | FastAPI + SQLite API in `vibe/`: register/login with JWT, list rooms, room availability, create/list/cancel bookings, admins create and edit rooms and cancel any booking, admin created via a CLI command. The agent wrote 21 tests and reported all passing. |
| Choices the agent made without being asked | Times without a timezone treated as UTC; no booking in the past; regular users can't cancel an ended booking; cancelled bookings kept with status `cancelled`; random JWT key if `ROOMAPI_SECRET_KEY` is unset. |
| Met expectations? | TODO |
| Issues (incorrect, incomplete or inefficient code) | TODO |
| Refinement and why | TODO (none yet: there has been only one round) |

Prompt (verbatim):

```text
Build a room booking REST API in Python with FastAPI and SQLite.

Users should be able to register and log in. Logged-in users can see a list of rooms, check when a room is available, book a room for a time slot, see their own bookings and cancel them. There should also be admin users who can create and edit rooms and cancel any booking.

Only read and write files inside the vibe/ folder. Do not touch anything outside it. Tell me how to run it.
```

<!-- Copy the Round 1 block for each later round. -->

## §3.3 Prompt iteration log

The template asks for at least one example where a prompt failed or hallucinated and how it was refined. One row per failure.

| # | Initial Prompt/Specification | AI Failure Mode / Bug Produced | Refined Prompt/Specification | Resulting Code Quality | What did not happen according to your plan (which task was not done) | Modified Prompt (how you modified it, and the modified prompt) |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
