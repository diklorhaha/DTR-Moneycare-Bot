from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    discord_token: str
    robux_rate: float
    ticket_channel_prefix: str
    ticket_tool_bot_id: int | None
    embed_wait_seconds: int
    payment_timeout_minutes: int
    payment_poll_interval_seconds: int
    yoomoney_wallet: str
    yoomoney_access_token: str
    yoomoney_payment_type: str
    yoomoney_quickpay_form: str
    yoomoney_payment_targets: str
    webhook_enabled: bool
    webhook_host: str
    webhook_port: int
    notification_secret: str
    ticket_close_mode: str
    msg_payment: str
    msg_success: str
    msg_timeout: str
    msg_embed_timeout: str
    msg_payment_error: str


def load_settings() -> Settings:
    load_dotenv()

    bot_id_raw = os.getenv("TICKET_TOOL_BOT_ID", "").strip()
    ticket_tool_bot_id: int | None
    if bot_id_raw:
        try:
            ticket_tool_bot_id = int(bot_id_raw)
        except ValueError as exc:
            raise RuntimeError("TICKET_TOOL_BOT_ID must be an integer snowflake") from exc
    else:
        ticket_tool_bot_id = None

    rate = float(_require("ROBUX_RATE"))
    if rate <= 0:
        raise RuntimeError("ROBUX_RATE must be > 0")

    close_mode = os.getenv("TICKET_CLOSE_MODE", "delete").strip().lower()
    if close_mode not in {"delete", "none"}:
        raise RuntimeError("TICKET_CLOSE_MODE must be 'delete' or 'none'")

    embed_wait = int(os.getenv("EMBED_WAIT_SECONDS", "120"))
    timeout_min = int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "30"))
    poll_sec = int(os.getenv("PAYMENT_POLL_INTERVAL_SECONDS", "20"))
    webhook_port = int(os.getenv("YOOMONEY_WEBHOOK_PORT", "8080"))
    if embed_wait < 1:
        raise RuntimeError("EMBED_WAIT_SECONDS must be >= 1")
    if timeout_min < 1:
        raise RuntimeError("PAYMENT_TIMEOUT_MINUTES must be >= 1")
    if poll_sec < 1:
        raise RuntimeError("PAYMENT_POLL_INTERVAL_SECONDS must be >= 1")
    if not (1 <= webhook_port <= 65535):
        raise RuntimeError("YOOMONEY_WEBHOOK_PORT must be 1..65535")

    return Settings(
        discord_token=_require("DISCORD_BOT_TOKEN"),
        robux_rate=rate,
        ticket_channel_prefix=os.getenv("TICKET_CHANNEL_PREFIX", "ticket-").strip().lower(),
        ticket_tool_bot_id=ticket_tool_bot_id,
        embed_wait_seconds=embed_wait,
        payment_timeout_minutes=timeout_min,
        payment_poll_interval_seconds=poll_sec,
        yoomoney_wallet=_require("YOOMONEY_WALLET"),
        yoomoney_access_token=_require("YOOMONEY_ACCESS_TOKEN"),
        yoomoney_payment_type=os.getenv("YOOMONEY_PAYMENT_TYPE", "AC").strip() or "AC",
        yoomoney_quickpay_form=os.getenv("YOOMONEY_QUICKPAY_FORM", "shop").strip() or "shop",
        yoomoney_payment_targets=os.getenv("YOOMONEY_PAYMENT_TARGETS", "Оплата Robux").strip(),
        webhook_enabled=_bool("YOOMONEY_WEBHOOK_ENABLED", False),
        webhook_host=os.getenv("YOOMONEY_WEBHOOK_HOST", "0.0.0.0").strip(),
        webhook_port=webhook_port,
        notification_secret=os.getenv("YOOMONEY_NOTIFICATION_SECRET", "").strip(),
        ticket_close_mode=close_mode,
        msg_payment=os.getenv(
            "MSG_PAYMENT",
            "Сумма к оплате: **{rub} ₽** (за {robux} R$)\n"
            "Оплатите по ссылке:\n{payment_url}\n\n"
            "Ожидание оплаты: {minutes} мин.",
        ),
        msg_success=os.getenv("MSG_SUCCESS", "Оплата получена. Спасибо! Заказ в обработке."),
        msg_timeout=os.getenv("MSG_TIMEOUT", "Время на оплату истекло. Тикет закрыт."),
        msg_embed_timeout=os.getenv(
            "MSG_EMBED_TIMEOUT",
            "Не удалось прочитать сумму робуксов из Ticket Tool. Обратитесь к администратору.",
        ),
        msg_payment_error=os.getenv(
            "MSG_PAYMENT_ERROR",
            "Не удалось создать ссылку на оплату. Попробуйте позже или напишите в поддержку.",
        ),
    )
