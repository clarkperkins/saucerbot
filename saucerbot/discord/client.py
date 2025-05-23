# -*- coding: utf-8 -*-
import logging
from typing import Any, TypeVar

import arrow
from discord import (
    Client,
    Guild,
    Intents,
    Interaction,
    Member,
    Message,
    Object,
    Reaction,
    TextChannel,
    User,
)
from discord.app_commands import CommandTree
from django.utils import timezone

from saucerbot.discord.models import Channel as SChannel
from saucerbot.discord.models import Guild as SGuild
from saucerbot.discord.models import HistoricalDisplayName

logger = logging.getLogger(__name__)

T = TypeVar("T")

CENTRAL_TIME = "US/Central"


class SaucerbotClient(Client):
    # pylint: disable=no-self-use

    def __init__(self, *, intents: Intents = Intents.all(), **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.tree = CommandTree(self)
        self.dev_guild_id: str | None = options.pop("dev_guild_id", None)

    async def setup_hook(self):
        if self.dev_guild_id:
            guild = Object(id=self.dev_guild_id)

            logger.info("Setting up commands")
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    async def on_ready(self):
        logger.info("Logged in as %s", self.user)

    async def lookup_guild(self, guild: Guild) -> SGuild:
        s_guild, _ = await SGuild.objects.aget_or_create(  # type: ignore
            guild_id=guild.id,
            defaults={
                "name": guild.name,
            },
        )
        return s_guild

    async def lookup_channel(self, guild: SGuild, channel: TextChannel) -> SChannel:
        s_channel, created = await SChannel.objects.aget_or_create(  # type: ignore
            guild=guild,
            channel_id=channel.id,
            defaults={
                "name": channel.name,
            },
        )
        if created:
            await s_channel.add_defaults()
        return s_channel

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

    async def on_reaction_add(self, reaction: Reaction, user: User | Member):
        logger.info("%s reacted to %s with %s", user, reaction.message, reaction)

    # async def on_reaction_remove(self, reaction: Reaction, user: User | Member):
    #     pass
    #
    # async def on_reaction_clear(self, message: Message, reactions: list[Reaction]):
    #     pass
    #
    # async def on_reaction_clear_emoji(self, reaction: Reaction):
    #     pass

    async def store_display_name(self, member: Member):
        await HistoricalDisplayName.objects.acreate(  # type: ignore
            guild_id=str(member.guild.id),
            user_id=str(member.id),
            timestamp=timezone.now(),
            display_name=member.display_name,
        )

    async def on_member_join(self, member: Member):
        await self.store_display_name(member)

    # async def on_member_remove(self, member: Member):
    #     pass

    async def on_member_update(self, before: Member, after: Member):
        # Only store the name if it actually changed!
        if after.display_name and before.display_name != after.display_name:
            await self.store_display_name(after)

    # async def on_user_update(self, before: User, after: User):
    #     pass
    #
    # async def on_guild_available(self, guild: Guild):
    #     pass
    #
    # async def on_guild_unavailable(self, guild: Guild):
    #     pass
    #
    # async def on_group_join(self, channel: GroupChannel, user: User):
    #     pass
    #
    # async def on_group_remove(self, channel: GroupChannel, user: User):
    #     pass


client = SaucerbotClient()


async def get_whoami_responses(guild_id: str, user_id: str) -> list[str]:
    response = ""

    display_names = HistoricalDisplayName.objects.filter(
        guild_id=guild_id,
        user_id=user_id,
    ).order_by("-timestamp")

    # We only care about central time!
    now = arrow.now(CENTRAL_TIME)

    responses = []

    async for display_name in display_names:  # type: ignore
        timestamp = arrow.get(display_name.timestamp)
        next_line = f"{display_name.display_name} {timestamp.humanize(now)}\n"
        if len(response) + len(next_line) > 2000:
            responses.append(response)
            response = next_line
        else:
            response += next_line

    if response:
        responses.append(response)

    return responses


@client.tree.command()
async def whoami(interaction: Interaction):
    if not interaction.channel or not interaction.channel.guild:
        logger.warning("Interaction missing channel or guild: %s", interaction)
        return

    responses = await get_whoami_responses(
        str(interaction.channel.guild.id), str(interaction.user.id)
    )

    logger.info("whoami responses (%d): %s", len(responses), responses)

    # make sure to post the rest at the end
    first = True

    for response in responses:
        if first:
            await interaction.response.send_message(response)
            first = False
        else:
            await interaction.followup.send(response)
