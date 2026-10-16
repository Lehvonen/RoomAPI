"""Time conversion and booking-window rules (spec FR-011, FR-012, FR-017; research R4, R5)."""

from datetime import date, datetime, timezone

from .config import BOOKING_HORIZON, CLOSING_TIME, MAX_BOOKING_LENGTH, OPENING_TIME, TIMEZONE


class BookingRuleError(Exception):
    """A broken booking rule. The message is plain English and names the rule (NFR-008)."""


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise BookingRuleError("Times must include a timezone offset, e.g. 2026-10-20T09:00+03:00")
    try:
        return value.astimezone(timezone.utc)
    except OverflowError:
        raise BookingRuleError("Time is out of the supported range") from None


def check_booking_window(start: datetime, end: datetime, now: datetime) -> tuple[datetime, datetime]:
    """Validate a requested booking and return (start, end) in UTC.

    The horizon is checked before any conversion, so a date near year 9999 is refused
    as "too far ahead" instead of overflowing (research R5).
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise BookingRuleError("Times must include a timezone offset, e.g. 2026-10-20T09:00+03:00")
    if end <= start:
        raise BookingRuleError("end_time must be after start_time")
    if start < now:
        raise BookingRuleError("Cannot book a time in the past")
    if start > now + BOOKING_HORIZON:
        raise BookingRuleError("Bookings can start at most 90 days ahead")
    if end - start > MAX_BOOKING_LENGTH:
        raise BookingRuleError("A booking can last at most 4 hours")

    start_utc, end_utc = to_utc(start), to_utc(end)
    start_local, end_local = start_utc.astimezone(TIMEZONE), end_utc.astimezone(TIMEZONE)
    if start_local.date() != end_local.date():
        raise BookingRuleError("A booking must start and end on the same day (Helsinki time)")
    opens, closes = opening_window(start_local.date())
    if start_utc < opens or end_utc > closes:
        raise BookingRuleError("Rooms can only be booked between 08:00 and 18:00 Helsinki time")
    return start_utc, end_utc


def opening_window(day: date) -> tuple[datetime, datetime]:
    """That Helsinki date's opening and closing time, in UTC. Follows summer and winter time."""
    opens = datetime.combine(day, OPENING_TIME, tzinfo=TIMEZONE)
    closes = datetime.combine(day, CLOSING_TIME, tzinfo=TIMEZONE)
    return opens.astimezone(timezone.utc), closes.astimezone(timezone.utc)
