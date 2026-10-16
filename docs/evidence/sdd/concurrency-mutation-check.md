# SDD: concurrency test mutation check (NFR-005, SC-002)

The test `sdd/tests/acceptance/test_nfr_concurrency.py` catches double-booking. Without the `BEGIN IMMEDIATE` write lock (research R1), 20 simultaneous requests for one free slot created up to 10 bookings. With it, exactly 1.

Run on 2026-10-16 on branch `feat/sdd-bookings` (#18). For the check, the line `connection.exec_driver_sql("BEGIN IMMEDIATE")` in `sdd/app/db.py` was temporarily replaced with `pass`, then restored with `git checkout -- app/db.py`. Nothing from the mutated version was committed.

| Run | Write lock | Bookings created for the same slot | Test |
|---|---|---|---|
| 1 | removed | 10 | failed (`assert 10 == 1`) |
| 2 | removed | 5 | failed (`assert 5 == 1`) |
| 3 | removed | 7 | failed (`assert 7 == 1`) |
| 4 | restored | 1 | passed |

Command: `uv run pytest -q tests/acceptance/test_nfr_concurrency.py` (from `sdd/`).
