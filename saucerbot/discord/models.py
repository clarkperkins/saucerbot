# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional, Union

import arrow
from asgiref.sync import async_to_sync, sync_to_async
from discord import Member as DMember, Message as DMessage, User as DUser
from discord.abc import Messageable
from discord.errors import HTTPException
from discord.http import HTTPClient
from django.contrib.auth import models as auth_models
from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.db.models.manager import EmptyManager
from django.utils import timezone
from django.utils.functional import cached_property

from saucerbot.discord.utils import refresh_token
from saucerbot.handlers import BotContext, Message, registry

logger = logging.getLogger(__name__)

SESSION_KEY = "_discord_user_id"


def _sending_done_callback(fut: asyncio.Future):
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
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
    def author(self) -> Union[DUser, DMember]:
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


class User(models.Model):
    access_token = models.CharField(max_length=64)
    token_type = models.CharField(max_length=64)
    refresh_token = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    user_id = models.CharField(max_length=32, unique=True)

    # User is always active
    is_active = True

    # Never staff or superuser
    is_staff = False
    is_superuser = False

    objects = models.Manager()
    _groups = EmptyManager(auth_models.Group)
    _user_permissions = EmptyManager(auth_models.Permission)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_info = None

    def __str__(self):
        return self.username

    def _check_expired(self):
        if timezone.now() + timedelta(minutes=5) > self.expires_at:
            # Need a new refresh token
            token_data = refresh_token(self.refresh_token)
            self.access_token = token_data["access_token"]
            self.token_type = token_data["token_type"]
            self.refresh_token = token_data["refresh_token"]
            self.expires_at = timezone.now() + timedelta(
                seconds=int(token_data["expires_in"])
            )
            self.save()

    async def _new_client(self):
        await sync_to_async(self._check_expired)()
        client = HTTPClient()
        self._user_info = await client.static_login(
            f"{self.token_type} {self.access_token}", bot=False
        )
        return client

    @property
    def user_info(self) -> dict[str, Any]:
        if self._user_info is None:
            self._check_expired()
            self._user_info = lookup_user_info(self.access_token, self.token_type)
        return self._user_info

    @property
    def username(self):
        return self.user_info.get("username")

    def get_username(self):
        return self.username

    @cached_property
    @async_to_sync
    async def guild_ids(self) -> list[str]:
        client = await self._new_client()
        guilds = await client.get_guilds(50)
        await client.close()
        return [g["id"] for g in guilds]

    @property
    def groups(self):
        return User._groups

    @property
    def user_permissions(self):
        return User._user_permissions

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True


class InvalidDiscordUser(SuspiciousOperation):
    pass


def get_user(request) -> Optional[User]:
    try:
        user_id = User._meta.pk.to_python(request.session[SESSION_KEY])  # type: ignore[union-attr]
        return User.objects.get(pk=user_id)
    except KeyError:
        pass
    except User.DoesNotExist:
        pass
    return None


@async_to_sync
async def lookup_user_info(access_token: str, token_type: str) -> dict[str, Any]:
    client = HTTPClient()
    user_info = await client.static_login(f"{token_type} {access_token}", bot=False)
    await client.close()
    return user_info


def new_user(
    request, access_token: str, token_type: str, refresh_token: str, expires_in: int
):
    try:
        user_data = lookup_user_info(access_token, token_type)
        user_id = str(user_data["id"])
    except HTTPException:
        raise InvalidDiscordUser("Invalid access token")

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
    name = models.CharField(max_length=128, db_index=True)


class Channel(models.Model):
    guild = models.ForeignKey(Guild, models.CASCADE, related_name="channels")
    channel_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64, db_index=True)

    async def handle_message(
        self, loop: asyncio.AbstractEventLoop, message: DMessage
    ) -> list[str]:
        handler_names = await loop.run_in_executor(
            None, lambda: [h.handler_name for h in self.handlers.all()]
        )

        matched_handlers: list[str] = []

        for handler in registry:
            if "discord" not in handler.platforms:
                continue

            if handler.name not in handler_names:
                continue

            # We already matched at least one handler, don't run this one
            if matched_handlers and not handler.always_run:
                continue

            logger.debug("Trying message handler %s ...", handler.name)

            matched = handler.run(
                DiscordBotContext(loop, message.channel),
                DiscordMessage(message),
            )

            # Keep track of the handlers that matched
            if matched:
                matched_handlers.append(handler.name)

        return matched_handlers


class Handler(models.Model):
    channel = models.ForeignKey(Channel, models.CASCADE, related_name="handlers")
    handler_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.channel_id} - {self.handler_name}"

    def __repr__(self):
        return f"Handler({self.channel_id}, {self.handler_name})"


class HistoricalNickname(models.Model):
    guild_id = models.CharField(max_length=64)
    user_id = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    nickname = models.CharField(max_length=256)

    class Meta:
        indexes = [
            models.Index(fields=("guild_id", "user_id")),
        ]

    def __str__(self):
        return f"{self.nickname} - {self.timestamp}"

    def __repr__(self):
        return f"HistoricalNickname({self.guild_id}, {self.user_id}, {self.timestamp}, {self.nickname})"
