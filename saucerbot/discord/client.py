# -*- coding: utf-8 -*-
import logging
from collections.abc import Awaitable
from typing import Union

from discord import (
    Client,
    GroupChannel,
    Guild,
    Intents,
    Member,
    Message,
    Reaction,
    TextChannel,
    User,
)

from saucerbot.discord.models import Channel as SChannel
from saucerbot.discord.models import Guild as SGuild

logger = logging.getLogger(__name__)


class SaucerbotClient(Client):
    def __init__(self):
        super().__init__(intents=Intents.all())

    async def on_ready(self):
        logger.info("Logged in as %s", self.user)

    @staticmethod
    def _lookup_guild(guild: Guild) -> SGuild:
        s_guild, _ = SGuild.objects.get_or_create(
            guild_id=guild.id,
            defaults={
                "name": guild.name,
            },
        )
        return s_guild

    def lookup_guild(self, guild: Guild) -> Awaitable[SGuild]:
        return self.loop.run_in_executor(None, self._lookup_guild, guild)

    @staticmethod
    def _lookup_channel(guild: SGuild, channel: TextChannel) -> SChannel:
        s_channel, _ = SChannel.objects.get_or_create(
            guild=guild,
            channel_id=channel.id,
            defaults={
                "name": channel.name,
            },
        )
        return s_channel

    def lookup_channel(
        self, guild: SGuild, channel: TextChannel
    ) -> Awaitable[SChannel]:
        return self.loop.run_in_executor(None, self._lookup_channel, guild, channel)

    async def on_message(self, message: Message):
        logger.info(
            "Message from %s in %s#%s: %s",
            message.author,
            message.guild,
            message.channel,
            message.content,
        )

        if message.author == self.user:
            return

        if message.guild:
            stored_guild = await self.lookup_guild(message.guild)
            if isinstance(message.channel, TextChannel):
                stored_channel = await self.lookup_channel(
                    stored_guild, message.channel
                )
                await stored_channel.handle_message(self.loop, message)

    async def on_reaction_add(self, reaction: Reaction, user: Union[User, Member]):
        logger.info("%s reacted to %s with %s", user, reaction.message, reaction)

    async def on_reaction_remove(self, reaction: Reaction, user: Union[User, Member]):
        pass

    async def on_reaction_clear(self, message: Message, reactions: list[Reaction]):
        pass

    async def on_reaction_clear_emoji(self, reaction: Reaction):
        pass

    async def on_member_join(self, member: Member):
        pass

    async def on_member_remove(self, member: Member):
        pass

    async def on_member_update(self, before: Member, after: Member):
        pass

    async def on_user_update(self, before: User, after: User):
        pass

    async def on_guild_available(self, guild: Guild):
        pass

    async def on_guild_unavailable(self, guild: Guild):
        pass

    async def on_group_join(self, channel: GroupChannel, user: User):
        pass

    async def on_group_remove(self, channel: GroupChannel, user: User):
        pass
