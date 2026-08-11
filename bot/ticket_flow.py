from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import discord

from bot import messages
from bot.config import Settings
from bot.embed_parser import (
    extract_robux_from_embeds,
    looks_like_ticket_channel,
    make_payment_label,
)
from bot.pricing import rubles_from_robux
from bot.yoomoney_client import YooMoneyClient, YooMoneyError

logger = logging.getLogger(__name__)


@dataclass
class ActivePayment:
    channel_id: int
    label: str
    robux: int
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event: asyncio.Event = field(default_factory=asyncio.Event)
    paid: bool = False


class TicketFlow:
    def __init__(self, settings: Settings, yoomoney: YooMoneyClient) -> None:
        self.settings = settings
        self.yoomoney = yoomoney
        self._handled_channels: set[int] = set()
        self._active: dict[str, ActivePayment] = {}
        self._channel_tasks: dict[int, asyncio.Task[None]] = {}
        self._robux_events: dict[int, asyncio.Event] = {}
        self._robux_values: dict[int, int] = {}

    async def mark_paid(self, label: str) -> None:
        payment = self._active.get(label)
        if payment is None:
            return
        payment.paid = True
        payment.event.set()

    async def on_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.TextChannel):
            return
        if not looks_like_ticket_channel(channel.name, self.settings.ticket_channel_prefix):
            return
        self._start_ticket(channel)

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or not isinstance(message.channel, discord.TextChannel):
            return
        channel = message.channel
        if not looks_like_ticket_channel(channel.name, self.settings.ticket_channel_prefix):
            return

        is_ticket_tool = (
            self.settings.ticket_tool_bot_id is None
            or message.author.id == self.settings.ticket_tool_bot_id
        )
        if is_ticket_tool and message.embeds:
            self._maybe_capture_robux(channel.id, message)

        # Подхват тикета, если channel_create пропущен (рестарт бота и т.п.)
        if channel.id not in self._handled_channels and is_ticket_tool and message.embeds:
            self._start_ticket(channel)

    def _start_ticket(self, channel: discord.TextChannel) -> None:
        if channel.id in self._handled_channels:
            return

        self._handled_channels.add(channel.id)
        self._robux_events[channel.id] = asyncio.Event()
        task = asyncio.create_task(self._run_ticket(channel), name=f"ticket-{channel.id}")
        self._channel_tasks[channel.id] = task
        task.add_done_callback(lambda done, cid=channel.id: self._on_ticket_done(done, cid))

    def _on_ticket_done(self, done: asyncio.Task[None], channel_id: int) -> None:
        self._channel_tasks.pop(channel_id, None)
        self._robux_events.pop(channel_id, None)
        self._robux_values.pop(channel_id, None)
        # канал можно снова обработать только после полного завершения (рестарт тикета редкий)
        self._handled_channels.discard(channel_id)
        if done.cancelled():
            return
        exc = done.exception()
        if exc is not None:
            logger.error("Ticket flow failed for channel %s", channel_id, exc_info=exc)

    def _maybe_capture_robux(self, channel_id: int, message: discord.Message) -> None:
        if not message.embeds:
            return
        robux = extract_robux_from_embeds(list(message.embeds))
        if robux is None:
            return
        self._robux_values[channel_id] = robux
        event = self._robux_events.get(channel_id)
        if event is not None:
            event.set()

    async def _run_ticket(self, channel: discord.TextChannel) -> None:
        try:
            robux = await self._wait_for_robux(channel)
            if robux is None:
                await self._safe_send(channel, messages.embed_timeout_message(self.settings))
                return

            rub = rubles_from_robux(robux, self.settings.robux_rate)
            label = make_payment_label(channel.id, robux)
            payment_url = self.yoomoney.build_payment_url(amount=rub, label=label)

            sent = await self._safe_send(
                channel,
                messages.payment_message(
                    self.settings,
                    robux=robux,
                    rub=rub,
                    payment_url=payment_url,
                ),
            )
            if not sent:
                return

            payment = ActivePayment(channel_id=channel.id, label=label, robux=robux)
            self._active[label] = payment
            try:
                paid = await self._await_payment(payment)
                if paid:
                    await self._safe_send(channel, messages.success_message(self.settings))
                else:
                    await self._safe_send(channel, messages.timeout_message(self.settings))
                    await self._close_ticket(channel)
            except YooMoneyError:
                logger.exception("YooMoney error while waiting for %s", label)
                await self._safe_send(channel, messages.payment_error_message(self.settings))
            finally:
                self._active.pop(label, None)
        except Exception:
            logger.exception("Unhandled ticket error in channel %s", channel.id)
            raise

    async def _wait_for_robux(self, channel: discord.TextChannel) -> int | None:
        if channel.id in self._robux_values:
            return self._robux_values[channel.id]

        found = await self._scan_history(channel)
        if found is not None:
            self._robux_values[channel.id] = found
            return found

        event = self._robux_events.setdefault(channel.id, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout=self.settings.embed_wait_seconds)
        except TimeoutError:
            return self._robux_values.get(channel.id) or await self._scan_history(channel)
        return self._robux_values.get(channel.id)

    async def _scan_history(self, channel: discord.TextChannel) -> int | None:
        try:
            async for message in channel.history(limit=30, oldest_first=True):
                if self.settings.ticket_tool_bot_id is not None:
                    if message.author.id != self.settings.ticket_tool_bot_id:
                        continue
                if not message.embeds:
                    continue
                robux = extract_robux_from_embeds(list(message.embeds))
                if robux is not None:
                    return robux
        except discord.Forbidden:
            logger.error("No permission to read history in %s", channel.id)
        except discord.HTTPException:
            logger.exception("Failed reading history in %s", channel.id)
        return None

    async def _await_payment(self, payment: ActivePayment) -> bool:
        timeout = self.settings.payment_timeout_minutes * 60
        poll_every = max(5, self.settings.payment_poll_interval_seconds)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            if payment.paid or payment.event.is_set():
                return True
            if await self.yoomoney.has_successful_payment(payment.label):
                payment.paid = True
                payment.event.set()
                return True

            remaining = deadline - loop.time()
            if remaining <= 0:
                return payment.paid

            try:
                await asyncio.wait_for(payment.event.wait(), timeout=min(poll_every, remaining))
                return True
            except TimeoutError:
                continue

    async def _safe_send(self, channel: discord.TextChannel, content: str) -> bool:
        try:
            await channel.send(content)
            return True
        except discord.NotFound:
            logger.warning("Channel %s gone, skip send", channel.id)
        except discord.Forbidden:
            logger.error("Cannot send messages in %s", channel.id)
        except discord.HTTPException:
            logger.exception("Failed to send message in %s", channel.id)
        return False

    async def _close_ticket(self, channel: discord.TextChannel) -> None:
        if self.settings.ticket_close_mode != "delete":
            return
        try:
            await channel.delete(reason="Payment timeout")
        except discord.NotFound:
            return
        except discord.Forbidden:
            logger.error("Cannot delete ticket channel %s (missing Manage Channels)", channel.id)
        except discord.HTTPException:
            logger.exception("Failed to delete ticket channel %s", channel.id)
