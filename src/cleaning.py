"""Small helper functions that clean single values."""
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")

# Date formats we expect in the raw files. %z reads "Z" and offsets like "+01:00".
# Values without a time zone are treated as UTC.
DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

STATUS_CODES = {"active": 0, "inactive": 1}


def split_name(full_name):
    """'Jane Doe' -> ('Jane', 'Doe'). Everything after the first word is the last name."""
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def clean_email(email):
    """Lowercase the email. Return None if it is not a valid email."""
    email = email.strip().lower()
    if EMAIL_PATTERN.match(email):
        return email
    return None


def to_iso8601(value):
    """Turn any of the known date formats into 'YYYY-MM-DDTHH:MM:SSZ'. Return None if unknown."""
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def to_statecode(status):
    """'active' -> 0, 'inactive' -> 1 (case-insensitive). Return None if unknown."""
    return STATUS_CODES.get(status.strip().lower())


def to_decimal(amount):
    """'250.50' -> Decimal('250.50'). Return None if it is not a real number (also 'NaN', 'Infinity')."""
    try:
        value = Decimal(amount.strip())
    except InvalidOperation:
        return None
    return value if value.is_finite() else None
