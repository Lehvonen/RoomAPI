"""Edge cases of the booking-window rules (FR-011, FR-012, FR-017) that black-box tests can't pin to the minute."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.timerules import BookingRuleError, check_booking_window, opening_window, to_utc

HEL = ZoneInfo("Europe/Helsinki")
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)  # fixed "now" so the edges are exact


def at(day: date, hh: int, mm: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=HEL)


DAY = date(2026, 10, 5)


# --- Opening hours boundaries ------------------------------------------------------


@pytest.mark.parametrize("start, end", [((8, 0), (9, 0)), ((17, 0), (18, 0)), ((8, 0), (12, 0))])
def test_bookings_touching_opening_and_closing_time_accepted(start, end):
    check_booking_window(at(DAY, *start), at(DAY, *end), NOW)


@pytest.mark.parametrize("start, end", [((7, 59), (9, 0)), ((17, 0), (18, 1))])
def test_one_minute_outside_opening_hours_refused(start, end):
    with pytest.raises(BookingRuleError, match="08:00 and 18:00"):
        check_booking_window(at(DAY, *start), at(DAY, *end), NOW)


# --- Length ------------------------------------------------------------------------


def test_exactly_four_hours_accepted():
    check_booking_window(at(DAY, 9), at(DAY, 13), NOW)


def test_overnight_booking_gets_the_same_day_message():
    with pytest.raises(BookingRuleError, match="same day"):
        check_booking_window(at(DAY, 17), at(date(2026, 10, 6), 9), NOW)


def test_four_hours_and_a_minute_refused():
    with pytest.raises(BookingRuleError, match="4 hours"):
        check_booking_window(at(DAY, 9), at(DAY, 13, 1), NOW)


# --- Order, past, horizon ------------------------------------------------------------


def test_end_must_be_after_start():
    with pytest.raises(BookingRuleError, match="after start_time"):
        check_booking_window(at(DAY, 10), at(DAY, 10), NOW)


def test_start_in_past_refused():
    with pytest.raises(BookingRuleError, match="past"):
        check_booking_window(NOW - timedelta(minutes=1), NOW + timedelta(minutes=30), NOW)


def test_start_exactly_90_days_ahead_accepted():
    start = NOW + timedelta(days=90)  # 2026-12-30 12:00 UTC = 14:00 Helsinki (winter time)
    check_booking_window(start, start + timedelta(hours=1), NOW)


def test_start_90_days_and_a_minute_ahead_refused():
    start = NOW + timedelta(days=90, minutes=1)
    with pytest.raises(BookingRuleError, match="90 days"):
        check_booking_window(start, start + timedelta(hours=1), NOW)


def test_year_9999_refused_without_overflow():
    start = datetime(9999, 12, 31, 23, 0, tzinfo=timezone(timedelta(hours=-5)))
    with pytest.raises(BookingRuleError, match="90 days"):
        check_booking_window(start, start + timedelta(minutes=30), NOW)


def test_naive_times_refused():
    with pytest.raises(BookingRuleError, match="offset"):
        check_booking_window(datetime(2026, 10, 5, 10), datetime(2026, 10, 5, 11), NOW)


def test_to_utc_out_of_range_is_a_rule_error():
    with pytest.raises(BookingRuleError, match="range"):
        to_utc(datetime(9999, 12, 31, 23, 0, tzinfo=timezone(timedelta(hours=-5))))


# --- Summer and winter time ------------------------------------------------------------


@pytest.mark.parametrize(
    "day, utc_open, utc_close",
    [
        (date(2026, 10, 24), "05:00", "15:00"),  # last day of summer time (UTC+3)
        (date(2026, 10, 25), "06:00", "16:00"),  # first day of winter time (UTC+2)
        (date(2027, 3, 27), "06:00", "16:00"),  # last day of winter time
        (date(2027, 3, 28), "05:00", "15:00"),  # first day of summer time
    ],
)
def test_opening_window_follows_local_clock_on_dst_days(day, utc_open, utc_close):
    opens, closes = opening_window(day)
    assert opens.strftime("%H:%M") == utc_open
    assert closes.strftime("%H:%M") == utc_close


def test_booking_on_dst_change_day_uses_local_hours():
    now = datetime(2026, 10, 20, tzinfo=timezone.utc)
    start, end = check_booking_window(at(date(2026, 10, 25), 8), at(date(2026, 10, 25), 12), now)
    assert (start.hour, end.hour) == (6, 10)  # 08:00–12:00 at UTC+2
