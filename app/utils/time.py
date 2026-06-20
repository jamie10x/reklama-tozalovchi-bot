from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hours_ago(hours: int) -> datetime:
    return utcnow() - timedelta(hours=hours)


def minutes_ago(minutes: int) -> datetime:
    return utcnow() - timedelta(minutes=minutes)
