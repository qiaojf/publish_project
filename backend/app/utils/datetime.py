from datetime import date, datetime, time, timezone


def start_of_day(value: date | None) -> datetime | None:
    return datetime.combine(value, time.min, tzinfo=timezone.utc) if value else None


def end_of_day(value: date | None) -> datetime | None:
    return datetime.combine(value, time.max, tzinfo=timezone.utc) if value else None
