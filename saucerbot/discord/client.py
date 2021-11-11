# -*- coding: utf-8 -*-
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TypeVar, Union

import arrow
from discord import Guild, Intents, Member, Message, Reaction, TextChannel, User
from django.utils import timezone

from saucerbot.discord.models import Channel as SChannel
from saucerbot.discord.models import Guild as SGuild
from saucerbot.discord.models import HistoricalDisplayName
from saucerbot.discord.overrides import ClientWithInteractions, Interaction

logger = logging.getLogger(__name__)

T = TypeVar("T")

CENTRAL_TIME = "US/Central"


def make_async(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to make a method of SaucerbotClient async.
    Should only decorate methods within the SaucerbotClient class.
    """

    @wraps(func)
    def wrapper(self, *args) -> Awaitable[T]:
        return self.loop.run_in_executor(None, func, self, *args)

    return wrapper


class SaucerbotClient(ClientWithInteractions):
    # pylint: disable=no-self-use

    def __init__(self, **kwargs):
        kwargs.setdefault("intents", Intents.all())
        super().__init__(**kwargs)

    async def on_ready(self):
        logger.info("Logged in as %s", self.user)

    @make_async
    def lookup_guild(self, guild: Guild) -> SGuild:
        s_guild, _ = SGuild.objects.get_or_create(
            guild_id=guild.id,
            defaults={
                "name": guild.name,
            },
        )
        return s_guild

    @make_async
    def lookup_channel(self, guild: SGuild, channel: TextChannel) -> SChannel:
        s_channel, created = SChannel.objects.get_or_create(
            guild=guild,
            channel_id=channel.id,
            defaults={
                "name": channel.name,
            },
        )
        if created:
            s_channel.add_defaults()
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

    @make_async
    def get_whoami_responses(self, guild_id: str, user_id: str) -> list[str]:
        response = ""

        display_names = HistoricalDisplayName.objects.filter(
            guild_id=guild_id,
            user_id=user_id,
        ).order_by("-timestamp")

        # We only care about central time!
        now = arrow.now(CENTRAL_TIME)

        responses = []

        for display_name in display_names:
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

    async def command_whoami(self, interaction: Interaction):
        responses = await self.get_whoami_responses(
            interaction.channel.guild.id, interaction.member.id
        )

        logger.info("%s", responses)

        # make sure to post the rest at the end
        first = True

        for response in responses:
            if first:
                await interaction.respond(response)
                first = False
            else:
                await interaction.follow_up(response)

    async def on_interaction(self, interaction: Interaction):
        logger.info("Interaction: %s", interaction.data)
        command_name = interaction.data["name"]

        coro = getattr(self, f"command_{command_name}", None)
        if coro:
            await coro(interaction)
        else:
            logger.error("No command named %s", command_name)

    async def on_reaction_add(self, reaction: Reaction, user: Union[User, Member]):
        logger.info("%s reacted to %s with %s", user, reaction.message, reaction)

    # async def on_reaction_remove(self, reaction: Reaction, user: Union[User, Member]):
    #     pass
    #
    # async def on_reaction_clear(self, message: Message, reactions: list[Reaction]):
    #     pass
    #
    # async def on_reaction_clear_emoji(self, reaction: Reaction):
    #     pass

    @make_async
    def store_display_name(self, member: Member):
        HistoricalDisplayName.objects.create(
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
