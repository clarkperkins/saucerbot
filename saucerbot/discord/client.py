# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from typing import Sequence, Union
from collections.abc import Coroutine

from discord import (
    Client,
    Emoji,
    GroupChannel,
    Guild,
    Intents,
    Invite,
    Member,
    Message,
    Reaction,
    Role,
    TextChannel,
    User,
    VoiceState,
)
from discord.abc import Messageable

from saucerbot.discord.models import Channel as SChannel, Guild as SGuild

logger = logging.getLogger(__name__)


class SaucerbotClient(Client):
    def __init__(self):
        super().__init__(intents=Intents.all())

    async def on_ready(self):
        logger.info("Logged in as %s", self.user)

    async def on_typing(
        self, channel: Messageable, user: Union[User, Member], when: datetime
    ):
        logger.info("%s is typing in %s", user, channel)

    @staticmethod
    def _lookup_guild(guild: Guild) -> SGuild:
        guild, _ = SGuild.objects.get_or_create(
            guild_id=guild.id,
            defaults={
                "name": guild.name,
            },
        )
        return guild

    def lookup_guild(self, guild: Guild) -> Coroutine[None, None, SGuild]:
        return self.loop.run_in_executor(None, self._lookup_guild, guild)

    @staticmethod
    def _lookup_channel(guild: SGuild, channel: TextChannel) -> SChannel:
        channel, _ = SChannel.objects.get_or_create(
            guild=guild,
            channel_id=channel.id,
            defaults={
                "name": channel.name,
            },
        )
        return channel

    def lookup_channel(
        self, guild: SGuild, channel: TextChannel
    ) -> Coroutine[None, None, SChannel]:
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

        stored_guild = await self.lookup_guild(message.guild)
        if isinstance(message.channel, TextChannel):
            stored_channel = await self.lookup_channel(stored_guild, message.channel)
            await stored_channel.handle_message(self.loop, message)

    async def on_message_edit(self, before: Message, after: Message):
        pass

    async def on_message_delete(self, message: Message):
        pass

    async def on_bulk_message_delete(self, messages: list[Message]):
        pass

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

    async def on_guild_join(self, guild: Guild):
        pass

    async def on_guild_remove(self, guild: Guild):
        pass

    async def on_guild_update(self, before: Guild, after: Guild):
        pass

    async def on_guild_role_create(self, role: Role):
        pass

    async def on_guild_role_delete(self, role: Role):
        pass

    async def on_guild_role_update(self, before: Role, after: Role):
        pass

    async def on_guild_emojis_update(
        self, guild: Guild, before: Sequence[Emoji], after: Sequence[Emoji]
    ):
        pass

    async def on_guild_available(self, guild: Guild):
        pass

    async def on_guild_unavailable(self, guild: Guild):
        pass

    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        pass

    async def on_member_ban(self, guild: Guild, user: Union[User, Member]):
        pass

    async def on_member_unban(self, guild: Guild, user: Union[User, Member]):
        pass

    async def on_invite_create(self, invite: Invite):
        pass

    async def on_invite_delete(self, invite: Invite):
        pass

    async def on_group_join(self, channel: GroupChannel, user: User):
        pass

    async def on_group_remove(self, channel: GroupChannel, user: User):
        pass
