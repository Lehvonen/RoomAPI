# SDD: login slow-down mutation checks (NFR-009)

Two of the slow-down tests passed before any slow-down existed, because there was no delay to misbehave. To show they still guard something, the implementation in `sdd/app/routers/auth.py` was broken on purpose, one way at a time. The tests were run, and the file was restored from a copy. Nothing from the mutated versions was committed.

Run on 2026-10-16 on branch `feat/sdd-nfr-evidence` (#21), with the delay at the spec's 2 seconds.

| Mutation | What it breaks | Guard test | Result |
|---|---|---|---|
| Wait while the database transaction is still open | Every other request waits behind a delayed login, so an attacker could slow everyone (vibe's N1b, in another form) | `test_a_delayed_login_does_not_block_other_requests` | failed: "bystander waited 1.78s behind the delayed login" |
| Don't clear failures after a successful login | The user stays slowed down after logging in correctly | `test_successful_login_clears_the_failures` | failed: next wrong attempt took 2.04 s (limit 1.0 s) |
| None (restored) | — | all 6 slow-down tests | passed |

Command: `uv run pytest -q tests/acceptance/test_nfr_login_slowdown.py` (from `sdd/`).
