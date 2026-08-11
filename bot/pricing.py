from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

_CODE_FENCE = re.compile(r"^`+|`+$")


def strip_embed_value(raw: str) -> str:
    text = raw.strip()
    return _CODE_FENCE.sub("", text).strip()


def parse_robux_amount(raw: str) -> int:
    cleaned = strip_embed_value(raw)
    cleaned = cleaned.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        raise ValueError(f"Cannot parse robux amount from: {raw!r}")
    value = Decimal(match.group(1))
    if value <= 0 or value != value.to_integral_value():
        raise ValueError(f"Robux amount must be a positive integer: {raw!r}")
    return int(value)


def rubles_from_robux(robux: int, rate: float) -> Decimal:
    if rate <= 0:
        raise ValueError("rate must be > 0")
    amount = Decimal(robux) / Decimal(str(rate))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_rub(amount: Decimal) -> str:
    if amount == amount.to_integral_value():
        return str(int(amount))
    return f"{amount:.2f}"
