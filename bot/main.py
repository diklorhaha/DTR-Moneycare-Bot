from __future__ import annotations

import logging

import discord

from bot.config import Settings, load_settings
from bot.ticket_flow import TicketFlow
from bot.webhook import NotificationServer
from bot.yoomoney_client import YooMoneyClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("bot")


class PaymentBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.message_content = True
        super().__init__(intents=intents)

        self.settings = settings
        self.yoomoney = YooMoneyClient(
            wallet=settings.yoomoney_wallet,
            access_token=settings.yoomoney_access_token,
            payment_type=settings.yoomoney_payment_type,
            quickpay_form=settings.yoomoney_quickpay_form,
            targets=settings.yoomoney_payment_targets,
        )
        self.flow = TicketFlow(settings, self.yoomoney)
        self._webhook: NotificationServer | None = None

    async def setup_hook(self) -> None:
        await self.yoomoney.__aenter__()
        if self.settings.webhook_enabled:
            if not self.settings.notification_secret:
                raise RuntimeError("YOOMONEY_NOTIFICATION_SECRET required when webhook enabled")
            self._webhook = NotificationServer(
                host=self.settings.webhook_host,
                port=self.settings.webhook_port,
                secret=self.settings.notification_secret,
                on_payment=self.flow.mark_paid,
            )
            await self._webhook.start()

    async def close(self) -> None:
        if self._webhook is not None:
            await self._webhook.stop()
        await self.yoomoney.__aexit__(None, None, None)
        await super().close()

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (%s)", self.user, self.user.id)

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        await self.flow.on_channel_create(channel)

    async def on_message(self, message: discord.Message) -> None:
        if self.user is not None and message.author.id == self.user.id:
            return
        await self.flow.on_message(message)


def main() -> None:
    settings = load_settings()
    bot = PaymentBot(settings)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
