from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote

from aiohttp import web

logger = logging.getLogger(__name__)

PaymentHandler = Callable[[str], Awaitable[None]]


def build_notification_sign(params: dict[str, str], secret: str) -> str:
    """HMAC-SHA256 по правилам ЮMoney HTTP-уведомлений (RFC 3986)."""
    items = [(k, v) for k, v in params.items() if k != "sign"]
    items.sort(key=lambda kv: kv[0])
    # ~ — unreserved в RFC 3986; буквы/цифры/_.- quote не трогает
    encoded = "&".join(f"{k}={quote(str(v), safe='~')}" for k, v in items)
    digest = hmac.new(secret.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest().lower()


def verify_notification(params: dict[str, Any], secret: str) -> bool:
    if not secret:
        return False
    received = str(params.get("sign") or "").lower()
    as_str = {str(k): str(v) for k, v in params.items()}
    expected = build_notification_sign(as_str, secret)
    return hmac.compare_digest(expected, received)


class NotificationServer:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        secret: str,
        on_payment: PaymentHandler,
    ) -> None:
        self.host = host
        self.port = port
        self.secret = secret
        self.on_payment = on_payment
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post("/yoomoney/notification", self._handle)
        app.router.add_get("/health", self._health)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        logger.info("YooMoney webhook listening on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    async def _health(self, _request: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def _handle(self, request: web.Request) -> web.Response:
        data = {str(k): str(v) for k, v in (await request.post()).items()}
        if not verify_notification(data, self.secret):
            logger.warning("Rejected YooMoney notification: bad signature")
            return web.Response(status=400, text="bad signature")

        label = data.get("label", "").strip()
        if label:
            task = asyncio.create_task(self.on_payment(label), name=f"paid-{label}")
            task.add_done_callback(self._log_payment_task)
        # ЮMoney считает уведомление принятым только при HTTP 200
        return web.Response(text="OK")

    @staticmethod
    def _log_payment_task(done: asyncio.Task[None]) -> None:
        if done.cancelled():
            return
        exc = done.exception()
        if exc is not None:
            logger.error("Payment webhook handler failed", exc_info=exc)
