from datetime import datetime
from decimal import Decimal


def parse_utc_datetime(dt_str: str) -> datetime:
    """Parse datetime string in UTC format"""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def cents_to_dollars(cents: str) -> Decimal:
    """Convert cents to dollars, handling None values"""
    return Decimal(cents) / 100


def get_difference_in_ms(start_time: datetime, end_time: datetime) -> int:
    """Get the difference in milliseconds between two datetime objects"""
    return int((end_time - start_time).total_seconds() * 1000)
