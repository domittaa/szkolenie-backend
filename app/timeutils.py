from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    """SQLite (local development, tests) returns naive datetimes, PostgreSQL aware ones."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)
