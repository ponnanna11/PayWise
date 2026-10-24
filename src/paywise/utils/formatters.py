"""
Formatting utilities for Indian financial notation and UI rendering.
"""
from datetime import date, datetime
from typing import Union


def format_inr(amount: Union[float, int]) -> str:
    """
    Formats a number into Indian Lakh/Crore numbering system.
    e.g. 1000000 -> ₹ 10,00,000.00
    """
    if amount is None:
        return "₹ 0.00"

    is_negative = amount < 0
    amount = abs(amount)
    amount_str = f"{amount:.2f}"
    parts = amount_str.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        # Group in pairs of 2 from the right
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3

    sign = "-" if is_negative else ""
    return f"{sign}₹ {formatted}.{decimal_part}"


def format_date(dt: Union[date, datetime, str]) -> str:
    if not dt:
        return "-"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    if isinstance(dt, datetime):
        return dt.strftime("%d %b %Y, %I:%M %p")
    if isinstance(dt, date):
        return dt.strftime("%d %b %Y")
    return str(dt)
