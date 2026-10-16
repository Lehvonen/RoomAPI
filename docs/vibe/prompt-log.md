# Vibe coding prompt log

Source material for report §3.2 (master prompts) and §3.3 (prompt iteration log).
Each round's agent output is kept as pasted in its own file (`round-N-output.md`).

Fill every `TODO` from what you actually did and saw. Nothing here should be reconstructed after the fact.

## §3.2 Prompts

### Round 1

| Field | Entry |
|---|---|
| Date | 2026-10-13 |
| Who prompted | Ivar Lehvonen |
| Tool / model | Claude Code (TODO: model name) |
| Commit | `75113b5` |
| Raw output | [`round-1-output.md`](round-1-output.md) (terminal paste, not verbatim; see the note at its top) |
| Purpose | TODO |
| Reasoning for the wording | TODO |
| Expected result | TODO |
| What came back | FastAPI + SQLite API in `vibe/`: register/login with JWT, list rooms, room availability, create/list/cancel bookings, admins create and edit rooms and cancel any booking, admin created via a CLI command. The agent wrote 21 tests and reported all passing. |
| Choices the agent made without being asked | Times without a timezone treated as UTC; no booking in the past; regular users can't cancel an ended booking; cancelled bookings kept with status `cancelled`; random JWT key if `ROOMAPI_SECRET_KEY` is unset. |
| Met expectations? | TODO |
| Issues (incorrect, incomplete or inefficient code) | Found afterwards by probing, not visible in the agent's own 21 tests: 3 inputs crash the server (HTTP 500), and 6 checks show rules the prompt left open that the agent filled in without asking, or not at all. See §3.3 and [`docs/evidence/vibe-round-1/findings.md`](../evidence/vibe-round-1/findings.md). |
| Refinement and why | TODO (none yet: there has been only one round) |

Prompt (verbatim):

```text
Build a room booking REST API in Python with FastAPI and SQLite.

Users should be able to register and log in. Logged-in users can see a list of rooms, check when a room is available, book a room for a time slot, see their own bookings and cancel them. There should also be admin users who can create and edit rooms and cancel any booking.

Only read and write files inside the vibe/ folder. Do not touch anything outside it. Tell me how to run it.
```

<!-- Copy the Round 1 block for each later round. -->

## §3.3 Prompt iteration log

The template asks for at least one example where a prompt failed or hallucinated and how it was refined. One row per failure. Same columns as report §3.3.

<!-- "What did not happen according to your plan": which task was not done.
"Modified Prompt": how you modified the prompt, and the modified prompt. -->

| Initial Prompt/Specification | AI Failure Mode / Bug Produced | Refined Prompt/Specification | Resulting Code Quality | What did not happen according to your plan | Modified Prompt |
|---|---|---|---|---|---|
| Round 1 prompt (§3.2) | Huge IDs (2^70) in a path or body crash the server with HTTP 500 (probe P4a, P4b) | TODO | TODO | TODO | TODO |
| Round 1 prompt (§3.2) | A booking near year 9999 overflows during the UTC conversion and crashes with HTTP 500 (probe P5) | TODO | TODO | TODO | TODO |
| Round 1 prompt (§3.2) | Deactivating a room leaves its future bookings active, while the owner can no longer see the room (probe P3) | TODO | TODO | TODO | TODO |
| Round 1 prompt (§3.2) | No booking rules beyond overlap: one user can book a room for 10 years or at 03:00 (probe P1, P2) | TODO | TODO | TODO | TODO |
| Round 1 prompt (§3.2) | Times without an offset are silently treated as UTC, so Helsinki times are stored 3 hours off (probe P6) | TODO | TODO | TODO | TODO |
| Round 1 prompt (§3.2) | Weak passwords accepted and no limit on failed logins (probe P7, P8) | TODO | TODO | TODO | TODO |
