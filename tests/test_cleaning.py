from decimal import Decimal

from cleaning import clean_email, split_name, to_decimal, to_iso8601, to_statecode


def test_split_name_trims_and_splits():
    assert split_name(" Charlie Brown") == ("Charlie", "Brown")
    assert split_name("Jane Doe") == ("Jane", "Doe")


def test_split_name_with_middle_name_keeps_rest_as_lastname():
    assert split_name("Anna Maria Schmidt") == ("Anna", "Maria Schmidt")


def test_clean_email_lowercases():
    assert clean_email("JOHN.SMITH@DOMAIN.COM") == "john.smith@domain.com"


def test_clean_email_invalid_returns_none():
    assert clean_email("invalid-email-format") is None


def test_to_iso8601_handles_all_three_formats():
    assert to_iso8601("2023-01-15T10:30:00Z") == "2023-01-15T10:30:00Z"
    assert to_iso8601("2023-02-20 14:15:00") == "2023-02-20T14:15:00Z"
    assert to_iso8601("2023-03-05") == "2023-03-05T00:00:00Z"


def test_to_iso8601_unknown_format_returns_none():
    assert to_iso8601("05.03.2023") is None


def test_to_statecode_is_case_insensitive():
    assert to_statecode("active") == 0
    assert to_statecode("ACTIVE") == 0
    assert to_statecode("inactive") == 1
    assert to_statecode("unknown") is None


def test_to_decimal():
    assert to_decimal("250.50") == Decimal("250.50")
    assert to_decimal("abc") is None
