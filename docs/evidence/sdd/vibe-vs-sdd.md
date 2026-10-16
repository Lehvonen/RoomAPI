# SDD acceptance suite: SDD version vs vibe version

The same black-box acceptance suite ran over HTTP against both versions on 2026-10-16: 155 tests that can run over HTTP, plus 11 that need the test database and were skipped. The SDD version passes all 155 that can run over HTTP. The vibe version (frozen at `b68a979`) passes 114 and fails 41. None of the 41 failures is a crash. 17 are interface differences, 11 are missing error documentation, and 13 are rules the vibe agent chose itself where the team's spec decided otherwise. Four of those 13 are login tests: vibe locks the account (429) instead of slowing it down, and in two of them a correct password is refused (N1).

## Runs

| Run | Server | Passed | Failed | Skipped | Raw result |
|---|---|---|---|---|---|
| In-process, with coverage | SDD (`sdd/`) | 186 | 0 | 0 | [`run-in-process.txt`](run-in-process.txt) (coverage 94.83%, gate 80%) |
| External HTTP | SDD, uvicorn | 155 | 0 | 11 | [`run-external-sdd.xml`](run-external-sdd.xml) |
| External HTTP | vibe `b68a979`, uvicorn | 114 | 41 | 11 | [`run-external-vibe.xml`](run-external-vibe.xml) |
| External HTTP, N1b test only | vibe, default settings | 0 | 1 | 0 | [`run-external-vibe-default-ip-limit.xml`](run-external-vibe-default-ip-limit.xml) |

The 11 skips are tests that read or write the test database directly (marked † in [traceability.md](../../../sdd/specs/001-room-booking-api/traceability.md)).

**Vibe configuration.** The full run raised only vibe's per-IP lockout limit (`ROOMAPI_LOGIN_MAX_FAILURES_PER_IP=1000000`, a setting vibe itself documents). Otherwise vibe's N1b weakness would have locked the test runner out after 20 failed logins, and every later test would have failed with 429. Vibe's per-user lockout stayed at its default of 5. N1b itself was then measured on its own with vibe's default settings: after 20 failed logins for non-existent usernames, a real user's correct password got 429. Nothing in `vibe/` was changed.

## Why the vibe version fails 41 tests

| Category | Tests | Kind |
|---|---|---|
| times returned with +03:00, not UTC Z | 5 | Interface difference |
| no GET /bookings/me (vibe lists own bookings at GET /bookings) | 4 | Interface difference |
| availability takes start/end, not date (date is ignored) | 7 | Interface difference |
| someone else's booking gives 404, not 403 | 1 | Interface difference |
| error responses not described in /openapi.json | 11 | Documentation |
| 07:00–20:00 and 8 h, not 08:00–18:00 and 4 h | 4 | Decision the spec made differently |
| no booking horizon | 1 | Decision the spec made differently |
| times without an offset read as Helsinki time | 1 | Decision the spec made differently |
| stricter passwords (5 distinct characters) | 2 | Decision the spec made differently |
| deactivation cancels bookings instead of being refused | 1 | Decision the spec made differently |
| lockout (429) instead of slow-down; a correct password refused in 2 (N1) | 4 | Decision the spec made differently |
| **Total** | **41** | |

Interface differences (17) are where the two versions expose the same feature differently. With the endpoint mapping in [contracts/api.md](../../../sdd/specs/001-room-booking-api/contracts/api.md) they would likely pass, so they say little about correctness. The 13 rule differences are the clearest SDD-vs-vibe contrast. Each one is a decision the team made on purpose in the spec (clarify answers on 2026-10-16), while the vibe agent made it alone, unasked.

## Every failing test

| Test | Category |
|---|---|
| `test_us1_accounts::test_register_creates_regular_user_without_password_in_response` | times returned with +03:00, not UTC Z |
| `test_us2_booking::test_book_free_slot` | times returned with +03:00, not UTC Z |
| `test_us2_booking::test_booking_belongs_to_the_booker` | times returned with +03:00, not UTC Z |
| `test_us2_booking::test_offset_input_returned_as_utc` | times returned with +03:00, not UTC Z |
| `test_us5_admin::test_admin_creates_active_room` | times returned with +03:00, not UTC Z |
| `test_us4_my_bookings::test_cancel_own_booking_frees_the_slot` | no GET /bookings/me (vibe lists own bookings at GET /bookings) |
| `test_us4_my_bookings::test_list_is_empty_for_new_user` | no GET /bookings/me (vibe lists own bookings at GET /bookings) |
| `test_us4_my_bookings::test_list_shows_only_my_bookings_oldest_first` | no GET /bookings/me (vibe lists own bookings at GET /bookings) |
| `test_us5_admin::test_admin_cancels_another_users_booking` | no GET /bookings/me (vibe lists own bookings at GET /bookings) |
| `test_us3_rooms_availability::test_bad_or_missing_date_gives_422[params0]` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_bad_or_missing_date_gives_422[params1]` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_bad_or_missing_date_gives_422[params2]` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_booking_at_opening_and_closing_leaves_no_edge_gaps` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_empty_day_is_free_during_opening_hours` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_one_booking_splits_the_free_time` | availability takes start/end, not date (date is ignored) |
| `test_us3_rooms_availability::test_two_bookings_give_three_free_intervals` | availability takes start/end, not date (date is ignored) |
| `test_us4_my_bookings::test_cancel_someone_elses_booking_forbidden` | someone else's booking gives 404, not 403 |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[delete-/bookings/{booking_id}]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[get-/bookings/me]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[get-/rooms/{room_id}/availability]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[get-/rooms/{room_id}]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[get-/users/me]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[patch-/rooms/{room_id}]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[post-/auth/login]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[post-/auth/register]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[post-/bookings]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_contract_endpoint_documented_with_its_errors[post-/rooms]` | error responses not described in /openapi.json |
| `test_nfr_docs::test_no_undocumented_endpoints` | error responses not described in /openapi.json |
| `test_us2_booking::test_booking_rules_refused_with_message[start0-end0-08:00]` | 07:00–20:00 and 8 h, not 08:00–18:00 and 4 h |
| `test_us2_booking::test_booking_rules_refused_with_message[start1-end1-08:00]` | 07:00–20:00 and 8 h, not 08:00–18:00 and 4 h |
| `test_us2_booking::test_booking_rules_refused_with_message[start2-end2-4 hours]` | 07:00–20:00 and 8 h, not 08:00–18:00 and 4 h |
| `test_us2_booking::test_booking_rules_refused_with_message[start3-end3-same day]` | 07:00–20:00 and 8 h, not 08:00–18:00 and 4 h |
| `test_us2_booking::test_horizon_90_days` | no booking horizon |
| `test_us2_booking::test_time_without_offset_refused` | times without an offset read as Helsinki time |
| `test_us1_accounts::test_password_length[10-201]` | stricter passwords (5 distinct characters) |
| `test_us1_accounts::test_password_length[128-201]` | stricter passwords (5 distinct characters) |
| `test_us5_admin::test_deactivation_refused_while_future_booking_exists` | deactivation cancels bookings instead of being refused |
| `test_nfr_login_slowdown::test_correct_password_still_logs_in_after_many_failures` | lockout (429) instead of slow-down; includes N1, a correct password refused |
| `test_nfr_login_slowdown::test_failures_count_regardless_of_letter_case` | lockout (429) instead of slow-down; includes N1, a correct password refused |
| `test_nfr_login_slowdown::test_sixth_failure_within_15_minutes_is_delayed` | lockout (429) instead of slow-down; includes N1, a correct password refused |
| `test_nfr_login_slowdown::test_successful_login_clears_the_failures` | lockout (429) instead of slow-down; includes N1, a correct password refused |

## How to reproduce

See [quickstart.md](../../../sdd/specs/001-room-booking-api/quickstart.md). In short: start the server with a fresh database and an admin `evidenceadmin`, then run (from `sdd/`):

```bash
ROOMAPI_BASE_URL=http://127.0.0.1:<port> ROOMAPI_TEST_ADMIN=evidenceadmin ROOMAPI_TEST_ADMIN_PASSWORD=Correct-horse-42 \
  uv run pytest tests/acceptance --junitxml=<file>.xml
```
