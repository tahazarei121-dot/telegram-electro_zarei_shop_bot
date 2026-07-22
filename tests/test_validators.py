"""تست‌های واحد برای توابع اعتبارسنجی ورودی‌ها."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.validators import (
    format_phone_number,
    validate_full_name,
    validate_phone_number,
    validate_price,
    validate_quantity,
    validate_stock,
    validate_text_length,
)


def test_validate_full_name_valid():
    valid, error = validate_full_name("علی رضایی")
    assert valid is True
    assert error is None


def test_validate_full_name_too_short():
    valid, error = validate_full_name("ع")
    assert valid is False
    assert error is not None


def test_validate_full_name_with_digits():
    valid, error = validate_full_name("علی 123")
    assert valid is False


def test_validate_phone_number_valid():
    valid, error = validate_phone_number("09123456789")
    assert valid is True


def test_validate_phone_number_invalid():
    valid, error = validate_phone_number("12345")
    assert valid is False


def test_format_phone_number_normalizes_country_code():
    assert format_phone_number("+989123456789") == "09123456789"
    assert format_phone_number("989123456789") == "09123456789"
    assert format_phone_number("9123456789") == "09123456789"


def test_validate_price_valid():
    valid, error, value = validate_price("150000")
    assert valid is True
    assert value == 150000


def test_validate_price_negative_or_zero():
    valid, error, value = validate_price("0")
    assert valid is False
    assert value is None


def test_validate_price_non_numeric():
    valid, error, value = validate_price("abc")
    assert valid is False


def test_validate_stock_valid():
    valid, error, value = validate_stock("25")
    assert valid is True
    assert value == 25


def test_validate_quantity_exceeds_max():
    valid, error, value = validate_quantity("1000", max_quantity=99)
    assert valid is False


def test_validate_quantity_within_max():
    valid, error, value = validate_quantity("5", max_quantity=99)
    assert valid is True
    assert value == 5


def test_validate_text_length_empty():
    valid, error = validate_text_length("   ", min_len=1, max_len=100, field_name="متن")
    assert valid is False


def test_validate_text_length_valid():
    valid, error = validate_text_length("یک متن معتبر", min_len=1, max_len=100, field_name="متن")
    assert valid is True
