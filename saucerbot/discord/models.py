# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import timedelta
from typing import Any

import arrow
from asgiref.sync import async_to_sync, sync_to_async
from discord import Member as DMember
from discord import Message as DMessage
from discord import User as DUser
from discord.abc import Messageable
from discord.errors import HTTPException
from discord.types import user
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from saucerbot.core.models import BaseUser, InvalidUser, get_user_builder
from saucerbot.discord.http import SaucerbotDiscordHTTPClient
from saucerbot.discord.utils import get_new_token
from saucerbot.handlers import BotContext, Message, registry

logger = logging.getLogger(__name__)

SESSION_KEY = "_discord_user_id"


def _sending_done_callback(fut: asyncio.Future):
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except asyncio.CancelledError:
        pass


class DiscordBotContext(BotContext):
    def __init__(self, loop: asyncio.AbstractEventLoop, messageable: Messageable):
        self.loop = loop
        self.messageable = messageable

    def post(self, message: Any):
        task = asyncio.ensure_future(self.messageable.send(message), loop=self.loop)
        task.add_done_callback(_sending_done_callback)


class DiscordMessage(Message):
    def __init__(self, discord_message: DMessage):
        self.discord_message = discord_message

    @property
    def author(self) -> DUser | DMember:
        return self.discord_message.author

    @property
    def user_id(self) -> str:
        return str(self.author.id)

    @property
    def user_name(self) -> str:
        return self.author.name

    @property
    def content(self) -> str:
        return self.discord_message.content

    @property
    def created_at(self) -> arrow.Arrow:
        return arrow.get(self.discord_message.created_at)


class User(BaseUser):
    access_token = models.CharField(max_length=64)
    token_type = models.CharField(max_length=64)
    refresh_token = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    user_id = models.CharField(max_length=32, unique=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_info = None

    def __str__(self):
        return self.username

    def _check_expired(self):
        if timezone.now() + timedelta(minutes=5) > self.expires_at:
            # Need a new refresh token
            token_data = get_new_token(self.refresh_token)
            self.access_token = token_data["access_token"]
            self.token_type = token_data["token_type"]
            self.refresh_token = token_data["refresh_token"]
            self.expires_at = timezone.now() + timedelta(
                seconds=int(token_data["expires_in"])
            )
            self.save()

    async def _new_client(self):
        await sync_to_async(self._check_expired)()
        client = SaucerbotDiscordHTTPClient(asyncio.get_running_loop())
        self._user_info = await client.user_login(self.token_type, self.access_token)
        return client

    @property
    def user_info(self) -> user.User:
        if self._user_info is None:
            self._check_expired()
            self._user_info = lookup_user_info(self.access_token, self.token_type)
        return self._user_info

    @property
    def username(self) -> str:
        return self.user_info["username"]

    @cached_property
    @async_to_sync
    async def guild_ids(self) -> list[str]:
        client = await self._new_client()
        guilds = await client.get_guilds(50)
        await client.close()
        return [str(g["id"]) for g in guilds]


get_user = get_user_builder(User, SESSION_KEY)


@async_to_sync
async def lookup_user_info(access_token: str, token_type: str) -> user.User:
    client = SaucerbotDiscordHTTPClient(asyncio.get_running_loop())
    user_info = await client.user_login(token_type, access_token)
    await client.close()
    return user_info


def new_user(
    request, access_token: str, token_type: str, refresh_token: str, expires_in: int
):
    try:
        user_data = lookup_user_info(access_token, token_type)
        user_id = str(user_data["id"])
    except HTTPException as e:
        raise InvalidUser("Invalid access token") from e

    # Either create the user, or update the given user with a new access token
    defaults = {
        "access_token": access_token,
        "token_type": token_type,
        "refresh_token": refresh_token,
        "expires_at": timezone.now() + timedelta(seconds=expires_in),
    }
    user, _ = User.objects.update_or_create(user_id=user_id, defaults=defaults)

    request.session[SESSION_KEY] = str(user.pk)


class Guild(models.Model):
    guild_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)


class Channel(models.Model):
    guild = models.ForeignKey(Guild, models.CASCADE, related_name="channels")
    channel_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)

    async def handle_message(
        self, loop: asyncio.AbstractEventLoop, message: DMessage
    ) -> list[str]:
        handler_names = await loop.run_in_executor(
            None, lambda: {h.handler_name for h in self.handlers.all()}
        )

        return registry.handle_message(
            "discord",
            handler_names,
            DiscordBotContext(loop, message.channel),
            DiscordMessage(message),
        )

    async def add_defaults(self):
        default_handlers = [
            Handler(channel=self, handler_name=h.name)
            for h in registry
            if h.on_by_default
        ]
        await self.handlers.abulk_create(default_handlers)


class Handler(models.Model):
    channel = models.ForeignKey(Channel, models.CASCADE, related_name="handlers")
    handler_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.channel_id} - {self.handler_name}"

    def __repr__(self):
        return f"Handler({self.channel_id}, {self.handler_name})"


class HistoricalDisplayName(models.Model):
    guild_id = models.CharField(max_length=64)
    user_id = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    display_name = models.CharField(max_length=256)

    class Meta:
        indexes = [
            models.Index(fields=("guild_id", "user_id")),
        ]

    def __str__(self):
        return f"{self.display_name} - {self.timestamp}"

    def __repr__(self):
        return (
            f"HistoricalDisplayName("
            f"{self.guild_id}, {self.user_id}, {self.timestamp}, {self.display_name}"
            f")"
        )
