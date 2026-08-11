from __future__ import annotations

from decimal import Decimal

from bot.config import Settings
from bot.pricing import format_rub


def payment_message(
    settings: Settings,
    *,
    robux: int,
    rub: Decimal,
    payment_url: str,
) -> str:
    return settings.msg_payment.format(
        robux=robux,
        rub=format_rub(rub),
        payment_url=payment_url,
        minutes=settings.payment_timeout_minutes,
    )


def success_message(settings: Settings) -> str:
    return settings.msg_success


def timeout_message(settings: Settings) -> str:
    return settings.msg_timeout


def embed_timeout_message(settings: Settings) -> str:
    return settings.msg_embed_timeout


def payment_error_message(settings: Settings) -> str:
    return settings.msg_payment_error
