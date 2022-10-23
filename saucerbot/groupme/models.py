# -*- coding: utf-8 -*-

import logging
from functools import lru_cache
from typing import Any

import arrow
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from lowerpines.endpoints.bot import Bot as LPBot
from lowerpines.endpoints.group import Group as LPGroup
from lowerpines.endpoints.message import Message as LPMessage
from lowerpines.endpoints.user import User as LPUser
from lowerpines.exceptions import UnauthorizedException
from lowerpines.gmi import GMI
from lowerpines.message import ComplexMessage
from scout_apm.api import Context

from saucerbot.core.models import BaseUser, InvalidUser, get_user_builder
from saucerbot.handlers import BotContext, Message, registry
from saucerbot.utils import get_tasted_brews

logger = logging.getLogger(__name__)

SESSION_KEY = "_groupme_user_id"


@lru_cache()
def get_gmi(access_token: str) -> GMI:
    return GMI(access_token)


class GroupMeBotContext(BotContext):
    def __init__(self, bot: LPBot):
        self.bot = bot

    def post(self, message: Any):
        if isinstance(message, (ComplexMessage, str)):
            self.bot.post(message)
        else:
            raise ValueError(f"Invalid message of type {type(message)}")


class GroupMeMessage(Message):
    def __init__(self, groupme_message: LPMessage):
        self.groupme_message = groupme_message

    @property
    def user_id(self) -> str:
        return self.groupme_message.user_id

    @property
    def user_name(self) -> str:
        return self.groupme_message.name

    @property
    def content(self) -> str:
        return self.groupme_message.text

    @property
    def created_at(self) -> arrow.Arrow:
        return arrow.get(self.groupme_message.created_at)


class User(BaseUser):
    access_token = models.CharField(max_length=64)
    user_id = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.groupme_user.name

    @cached_property
    def groupme_user(self) -> LPUser:
        return self.gmi.user.get()

    @property
    def username(self):
        return self.groupme_user.user_id

    @property
    def gmi(self):
        return get_gmi(self.access_token)


get_user = get_user_builder(User, SESSION_KEY)


def new_user(request, access_token: str):
    try:
        user: User | None = User.objects.get(access_token=access_token)
    except User.DoesNotExist:
        user = None

    if user is None:
        gmi = get_gmi(access_token)
        try:
            user_id = gmi.user.get().user_id
        except UnauthorizedException as e:
            raise InvalidUser("Invalid access token") from e

        # Either create the user, or update the given user with a new access token
        defaults = {"access_token": access_token}
        user, _ = User.objects.update_or_create(user_id=user_id, defaults=defaults)

    request.session[SESSION_KEY] = str(user.pk)


def _callback_url(slug: str) -> str:
    path = reverse("groupme:bot-callback", kwargs={"slug": slug})
    return f"https://{settings.SERVER_DOMAIN}{path}"


class BotManager(models.Manager):
    def create(self, **kwargs):
        owner = kwargs.get("owner")
        name = kwargs.get("name")
        slug = kwargs.get("slug")
        group = kwargs.pop("group", None)
        avatar_url = kwargs.pop("avatar_url", None)

        # Auto populate a slug if not given
        if not slug:
            slug = slugify(name)
            kwargs["slug"] = slug

        if "bot_id" not in kwargs and owner and name and slug and group:
            callback_url = _callback_url(slug)
            bot = owner.gmi.bots.create(group, name, callback_url, avatar_url)
            kwargs["bot_id"] = bot.bot_id
            kwargs["group_id"] = group.group_id

        return super().create(**kwargs)


class Bot(models.Model):
    owner = models.ForeignKey(User, models.CASCADE, related_name="bots")
    bot_id = models.CharField(max_length=32)
    group_id = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, unique=True)

    objects = BotManager()

    def __str__(self):
        return f"{self.name} (slug={self.slug})"

    def __repr__(self):
        return f"Bot({self.bot_id}, {self.name}, {self.slug}, {self.owner_id})"

    @cached_property
    def bot(self) -> LPBot:
        return self.owner.gmi.bots.get(bot_id=self.bot_id)  # pylint: disable=no-member

    @cached_property
    def group(self) -> LPGroup:
        return self.owner.gmi.groups.get(
            group_id=self.group_id
        )  # pylint: disable=no-member

    def post_message(self, message: ComplexMessage | str) -> None:
        self.bot.post(message)

    def handle_message(self, message: LPMessage) -> list[str]:
        other_bot_names = [b.name for b in Bot.objects.filter(group_id=self.group_id)]

        # We don't want to respond to any other bot in the same group
        if message.sender_type == "bot" and message.name in other_bot_names:
            return []

        handler_names = {h.handler_name for h in self.handlers.all()}

        matched_handlers = registry.handle_message(
            "groupme",
            handler_names,
            GroupMeBotContext(self.bot),
            GroupMeMessage(message),
        )

        if matched_handlers:
            Context.add("handlers", matched_handlers)

        return matched_handlers

    def update_bot(self, avatar_url: str | None) -> None:
        self.bot.name = self.name
        self.bot.callback_url = _callback_url(self.slug)
        self.bot.avatar_url = avatar_url
        self.bot.save()


class Handler(models.Model):
    bot = models.ForeignKey(Bot, models.CASCADE, related_name="handlers")
    handler_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.bot_id} - {self.handler_name}"

    def __repr__(self):
        return f"Handler({self.bot_id}, {self.handler_name})"


class SaucerUser(models.Model):
    groupme_id = models.CharField(max_length=32, unique=True)
    saucer_id = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.saucer_id} - {self.groupme_id}"

    def __repr__(self):
        return f"SaucerUser({self.groupme_id}, {self.saucer_id})"

    def get_brews(self):
        return get_tasted_brews(self.saucer_id)


class HistoricalNickname(models.Model):
    group_id = models.CharField(max_length=32)
    groupme_id = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    nickname = models.CharField(max_length=256)

    class Meta:
        indexes = [
            models.Index(fields=("group_id", "groupme_id")),
        ]

    def __str__(self):
        return f"{self.nickname} - {self.timestamp}"

    def __repr__(self):
        return (
            f"HistoricalNickname("
            f"{self.group_id}, {self.groupme_id}, {self.timestamp}, {self.nickname}"
            f")"
        )
