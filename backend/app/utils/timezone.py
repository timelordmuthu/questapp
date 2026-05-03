"""
backend/app/utils/timezone.py

Timezone helpers for per-user date math.
All datetimes stored as UTC in the DB; convert per-user in the app layer.
"""

from datetime import date, datetime, timedelta

import pytz


def now_in_tz(timezone_str: str) -> datetime:
    """Current datetime in the given IANA timezone."""
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz)


def today_in_tz(timezone_str: str) -> date:
    """Today's date in the given IANA timezone."""
    return now_in_tz(timezone_str).date()


def start_of_day_utc(user_date: date, timezone_str: str) -> datetime:
    """Midnight of user_date in the user's timezone, returned as UTC."""
    tz = pytz.timezone(timezone_str)
    local_midnight = tz.localize(datetime(user_date.year, user_date.month, user_date.day, 0, 0, 0))
    return local_midnight.astimezone(pytz.utc)


def end_of_day_utc(user_date: date, timezone_str: str) -> datetime:
    """23:59:59 of user_date in the user's timezone, returned as UTC."""
    tz = pytz.timezone(timezone_str)
    local_eod = tz.localize(datetime(user_date.year, user_date.month, user_date.day, 23, 59, 59))
    return local_eod.astimezone(pytz.utc)


def week_start_sunday(user_date: date) -> date:
    """Return the Sunday of the week containing user_date (Sun=0, Sat=6)."""
    # Python weekday: Mon=0, Sun=6 — adjust to treat Sunday as start
    days_since_sunday = (user_date.weekday() + 1) % 7
    return user_date - timedelta(days=days_since_sunday)


def week_end_saturday(week_start: date) -> date:
    """Return the Saturday (23:59:59) of the week starting on week_start."""
    return week_start + timedelta(days=6)


def utc_to_user_tz(dt: datetime, timezone_str: str) -> datetime:
    """Convert a UTC-aware datetime to the user's local timezone."""
    tz = pytz.timezone(timezone_str)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz)


def is_same_day_in_tz(dt: datetime, d: date, timezone_str: str) -> bool:
    """Check if a UTC datetime falls on the given date in the user's timezone."""
    local_dt = utc_to_user_tz(dt, timezone_str)
    return local_dt.date() == d
