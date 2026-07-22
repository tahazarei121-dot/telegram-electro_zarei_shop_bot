"""توابع اعتبارسنجی ورودی‌های کاربر."""

import re
from typing import Optional, Tuple


IRAN_PHONE_REGEX = re.compile(r"^(?:\+98|0)?9\d{9}$")


def normalize_digits(text: str) -> str:
    """تبدیل ارقام فارسی/عربی به ارقام انگلیسی برای پردازش یکسان."""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    result = text
    for i, digit in enumerate(persian_digits):
        result = result.replace(digit, str(i))
    for i, digit in enumerate(arabic_digits):
        result = result.replace(digit, str(i))
    return result


def validate_full_name(text: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی نام و نام خانوادگی کاربر."""
    text = text.strip()
    if len(text) < 3:
        return False, "نام وارد شده خیلی کوتاه است. لطفاً نام و نام خانوادگی کامل را وارد کنید."
    if len(text) > 100:
        return False, "نام وارد شده بیش از حد طولانی است."
    if any(char.isdigit() for char in normalize_digits(text)):
        return False, "نام نباید شامل عدد باشد. لطفاً دوباره وارد کنید."
    return True, None


def validate_phone_number(text: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی شماره موبایل ایرانی."""
    normalized = normalize_digits(text.strip()).replace(" ", "").replace("-", "")
    if not IRAN_PHONE_REGEX.match(normalized):
        return False, "شماره موبایل نامعتبر است. لطفاً به فرمت 09xxxxxxxxx وارد کنید."
    return True, None


def format_phone_number(text: str) -> str:
    """یکسان‌سازی فرمت شماره موبایل به شکل 09xxxxxxxxx."""
    normalized = normalize_digits(text.strip()).replace(" ", "").replace("-", "")
    if normalized.startswith("+98"):
        normalized = "0" + normalized[3:]
    elif normalized.startswith("98"):
        normalized = "0" + normalized[2:]
    elif not normalized.startswith("0"):
        normalized = "0" + normalized
    return normalized


def validate_price(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """اعتبارسنجی قیمت وارد شده (باید عدد صحیح مثبت باشد)."""
    normalized = normalize_digits(text.strip()).replace(",", "").replace("،", "")
    if not normalized.isdigit():
        return False, "قیمت باید یک عدد صحیح و مثبت باشد. لطفاً دوباره وارد کنید.", None
    value = int(normalized)
    if value <= 0:
        return False, "قیمت باید بزرگ‌تر از صفر باشد.", None
    if value > 10_000_000_000:
        return False, "مقدار وارد شده برای قیمت بیش از حد بزرگ است.", None
    return True, None, value


def validate_stock(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """اعتبارسنجی موجودی وارد شده (باید عدد صحیح غیرمنفی باشد)."""
    normalized = normalize_digits(text.strip())
    if not normalized.isdigit():
        return False, "موجودی باید یک عدد صحیح باشد. لطفاً دوباره وارد کنید.", None
    value = int(normalized)
    if value > 1_000_000:
        return False, "مقدار وارد شده برای موجودی بیش از حد بزرگ است.", None
    return True, None, value


def validate_quantity(text: str, max_quantity: int) -> Tuple[bool, Optional[str], Optional[int]]:
    """اعتبارسنجی تعداد درخواستی برای سبد خرید."""
    normalized = normalize_digits(text.strip())
    if not normalized.isdigit():
        return False, "تعداد باید یک عدد صحیح باشد.", None
    value = int(normalized)
    if value <= 0:
        return False, "تعداد باید بزرگ‌تر از صفر باشد.", None
    if value > max_quantity:
        return False, f"حداکثر تعداد مجاز برای هر کالا {max_quantity} عدد است.", None
    return True, None, value


def validate_text_length(text: str, min_len: int = 1, max_len: int = 1000,
                          field_name: str = "متن") -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی طول یک متن آزاد."""
    stripped = text.strip()
    if len(stripped) < min_len:
        return False, f"{field_name} نمی‌تواند خالی باشد."
    if len(stripped) > max_len:
        return False, f"{field_name} نباید بیش از {max_len} کاراکتر باشد."
    return True, None


def sanitize_text(text: str) -> str:
    """پاک‌سازی ورودی متنی از کاراکترهای کنترلی خطرناک، بدون حذف اموجی یا فارسی."""
    return "".join(ch for ch in text if ch.isprintable() or ch in "\n\t").strip()
