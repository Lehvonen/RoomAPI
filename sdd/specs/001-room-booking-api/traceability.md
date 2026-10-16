# Traceability: requirements → tests

Every functional requirement, non-functional requirement and success criterion in [spec.md](spec.md) maps to at least one automated test (constitution II, SC-003). Test files are in `sdd/tests/`. The suite has 186 tests, all passing. Tests marked † read or write the test database directly, so they are skipped against an external server.

## Functional requirements

| ID | Requirement (short) | Tests |
|---|---|---|
| FR-001 | Register; username rules; unique regardless of case | `acceptance/test_us1_accounts.py`: `test_register_creates_regular_user_without_password_in_response`, `test_username_taken_regardless_of_case`, `test_invalid_usernames_refused`, `test_username_length_boundaries_accepted`, `test_login_is_case_insensitive_on_username` |
| FR-002 | Password 10–128 characters | `test_us1_accounts.py::test_password_length` |
| FR-003 | Login gives a 60-minute token; no logout | `test_us1_accounts.py::test_login_returns_bearer_token_valid_for_60_minutes`, `test_profile_with_expired_token_refused`† |
| FR-004 | Same refusal for a wrong password and an unknown user | `test_us1_accounts.py::test_wrong_password_and_unknown_user_get_the_same_refusal` |
| FR-005 | Own profile, no password data | `test_us1_accounts.py::test_profile_shows_user_and_no_password_data`, `test_register_creates_regular_user_without_password_in_response` |
| FR-006 | Admins only from the operator CLI | `test_us1_accounts.py::test_registration_ignores_admin_request`; the CLI is used by the `admin` fixture in `conftest.py` |
| FR-007 | List and get active rooms | `acceptance/test_us3_rooms_availability.py`: `test_list_shows_only_active_rooms_by_name`†, `test_list_includes_new_room_with_its_details`, `test_get_active_room`, `test_inactive_room_hidden_from_users`, `test_missing_room_404` |
| FR-008 | Admins create and edit rooms; names unique regardless of case | `acceptance/test_us5_admin.py`: `test_admin_creates_active_room`, `test_admin_edits_room`, `test_invalid_room_fields_refused`, `test_invalid_edits_refused`, `test_duplicate_name_refused_on_create`, `test_duplicate_name_refused_on_rename`, `test_edit_missing_room_404` |
| FR-009 | Deactivate and reactivate; refused while bookings exist | `test_us5_admin.py`: `test_deactivation_refused_while_future_booking_exists`, `test_deactivated_room_hidden_and_unbookable_then_reactivated`, `test_ended_bookings_do_not_block_deactivation`†; `test_us2_booking.py::test_inactive_room_refused`; `test_us3_rooms_availability.py::test_availability_of_inactive_room_404` |
| FR-010 | Availability within opening hours for a Helsinki date, in UTC | `test_us3_rooms_availability.py`: `test_empty_day_is_free_during_opening_hours`, `test_one_booking_splits_the_free_time`, `test_two_bookings_give_three_free_intervals`, `test_booking_at_opening_and_closing_leaves_no_edge_gaps`, `test_other_days_bookings_not_shown`, `test_bad_or_missing_date_gives_422`, `test_availability_of_missing_room_404` |
| FR-011 | Book an active room: end after start, not in the past, ≤ 90 days ahead | `acceptance/test_us2_booking.py`: `test_book_free_slot`, `test_end_not_after_start_refused`, `test_start_in_past_refused`, `test_horizon_90_days`, `test_missing_room_refused`, `test_booking_belongs_to_the_booker`; `unit/test_timerules.py`: `test_end_must_be_after_start`, `test_start_in_past_refused`, `test_start_exactly_90_days_ahead_accepted`, `test_start_90_days_and_a_minute_ahead_refused` |
| FR-012 | 08:00–18:00 Helsinki, same day, ≤ 4 hours | `test_us2_booking.py`: `test_within_opening_hours_and_four_hours_accepted`, `test_booking_rules_refused_with_message`; `unit/test_timerules.py`: `test_bookings_touching_opening_and_closing_time_accepted`, `test_one_minute_outside_opening_hours_refused`, `test_exactly_four_hours_accepted`, `test_four_hours_and_a_minute_refused`, `test_overnight_booking_gets_the_same_day_message`, `test_opening_window_follows_local_clock_on_dst_days`, `test_booking_on_dst_change_day_uses_local_hours` |
| FR-013 | No overlaps (half-open ranges), also under simultaneous requests | `test_us2_booking.py`: `test_overlapping_booking_refused`, `test_any_overlap_shape_refused`, `test_back_to_back_bookings_allowed`, `test_same_slot_in_another_room_allowed`; `test_us4_my_bookings.py::test_cancel_own_booking_frees_the_slot`; `acceptance/test_nfr_concurrency.py` |
| FR-014 | My upcoming bookings, oldest first | `acceptance/test_us4_my_bookings.py`: `test_list_shows_only_my_bookings_oldest_first`, `test_list_is_empty_for_new_user`, `test_list_leaves_out_ended_bookings`† |
| FR-015 | Cancel own (not ended) or any as admin; kept with who and when | `test_us4_my_bookings.py`: `test_cancel_own_booking_frees_the_slot`, `test_cancelled_booking_is_kept_with_who_and_when`†, `test_cancel_twice_refused`, `test_cancel_ended_booking_refused_for_user`†, `test_cancel_missing_booking_404`; `test_us5_admin.py`: `test_admin_cancels_another_users_booking`, `test_admin_cancellation_records_the_admin`†, `test_admin_cancels_ended_booking`† |
| FR-016 | Bookings can't be edited | `test_us4_my_bookings.py::test_no_edit_endpoint`; `test_nfr_docs.py::test_no_undocumented_endpoints` |
| FR-017 | Offsets required; output in UTC | `test_us2_booking.py`: `test_time_without_offset_refused`, `test_offset_input_returned_as_utc`; `unit/test_timerules.py::test_naive_times_refused` |

## Non-functional requirements

| ID | Requirement (short) | Tests |
|---|---|---|
| NFR-001 | Salted Argon2id hashes; never returned or logged | `acceptance/test_nfr_security.py`: `test_stored_hash_is_salted_argon2id`†, `test_no_response_contains_the_password` |
| NFR-002 | Token required everywhere except register, login, health | `test_us1_accounts.py`: `test_profile_without_token_refused`, `test_profile_with_tampered_signature_refused`, `test_profile_with_tampered_claims_refused`, `test_profile_with_expired_token_refused`†; `test_rooms_need_token`, `test_booking_needs_token`, `test_list_needs_token`, `test_cancel_needs_token`, `test_room_management_needs_token`; `test_health.py::test_health_needs_no_token` |
| NFR-003 | Per-resource authorization | `test_us4_my_bookings.py::test_cancel_someone_elses_booking_forbidden`; `test_us5_admin.py`: `test_regular_user_cannot_create_room`, `test_regular_user_cannot_edit_room` |
| NFR-004 | No server error on any client input | `acceptance/test_nfr_invalid_input.py` (all 9 tests); `test_far_future_date_gives_422_not_500`, `test_huge_room_id_gives_422` (US2, US3), `test_cancel_huge_id_gives_422`, `test_edit_huge_room_id_gives_422`; `unit/test_timerules.py`: `test_year_9999_refused_without_overflow`, `test_to_utc_out_of_range_is_a_rule_error` |
| NFR-005 | Overlap protection holds under simultaneous requests | `acceptance/test_nfr_concurrency.py`; mutation check in [`docs/evidence/sdd/concurrency-mutation-check.md`](../../../docs/evidence/sdd/concurrency-mutation-check.md) |
| NFR-006 | Each request < 500 ms with 1,000 bookings | `acceptance/test_nfr_performance.py`† |
| NFR-007 | Self-documenting interface | `acceptance/test_nfr_docs.py`: `test_contract_endpoint_documented_with_its_errors`, `test_no_undocumented_endpoints`, `test_interactive_docs_available` |
| NFR-008 | Plain-English errors naming the rule | `test_nfr_invalid_input.py` (every error carries a message); `test_us2_booking.py::test_booking_rules_refused_with_message`, `test_start_in_past_refused`, `test_horizon_90_days`; `test_us5_admin.py::test_deactivation_refused_while_future_booking_exists` |
| NFR-009 | Login slow-down, never a lockout, never blocking others | `acceptance/test_nfr_login_slowdown.py` (all 6 tests); `test_us1_accounts.py::test_failed_login_username_stored_lower_case_and_at_most_50_characters`†; mutation checks in [`docs/evidence/sdd/login-slowdown-mutation-check.md`](../../../docs/evidence/sdd/login-slowdown-mutation-check.md) |

## Success criteria

| ID | Criterion | Evidence |
|---|---|---|
| SC-001 | Register, log in and book in under 2 minutes using only the interface description | Manual walkthrough in [quickstart.md](quickstart.md), "Manual smoke test"; the description itself is checked by `test_nfr_docs.py` |
| SC-002 | 20 simultaneous requests → exactly 1 booking | `acceptance/test_nfr_concurrency.py` |
| SC-003 | Every FR and NFR maps to a passing test | This table; CI runs the whole suite on every pull request |
| SC-004 | Zero server errors on the invalid-input set | `acceptance/test_nfr_invalid_input.py` |
| SC-005 | ≥ 80% coverage | CI gate `--cov-fail-under=80` in `.github/workflows/sdd-tests.yml`; currently 95% |
