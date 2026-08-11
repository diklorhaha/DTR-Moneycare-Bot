from __future__ import annotations

import re
from typing import Any

from bot.pricing import parse_robux_amount

ROBUX_FIELD_HINT = "сумма робуксов"
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9_-]+")


def _field_name(field: Any) -> str:
    name = getattr(field, "name", None)
    if name is None and isinstance(field, dict):
        name = field.get("name")
    return str(name or "")


def _field_value(field: Any) -> str:
    value = getattr(field, "value", None)
    if value is None and isinstance(field, dict):
        value = field.get("value")
    return str(value or "")


def _iter_fields(embed: Any) -> list[Any]:
    fields = getattr(embed, "fields", None)
    if fields is None and isinstance(embed, dict):
        fields = embed.get("fields") or []
    return list(fields or [])


def extract_robux_from_embeds(embeds: list[Any]) -> int | None:
    """Ищет поле «Сумма робуксов для покупки:» во всех embeds (включая 2-й)."""
    for embed in embeds:
        for field in _iter_fields(embed):
            name = _field_name(field)
            if ROBUX_FIELD_HINT not in name.casefold():
                continue
            try:
                return parse_robux_amount(_field_value(field))
            except ValueError:
                continue
    return None


def looks_like_ticket_channel(name: str, prefix: str) -> bool:
    return name.casefold().startswith(prefix.casefold())


def make_payment_label(channel_id: int, robux: int) -> str:
    """Уникальная метка ≤64 символов для Quickpay / operation-history."""
    label = f"t{channel_id}-r{robux}"
    return _NON_ALNUM.sub("-", label)[:64]
