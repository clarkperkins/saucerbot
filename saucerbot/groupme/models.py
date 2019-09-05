# -*- coding: utf-8 -*-

import inspect
import logging
from functools import lru_cache
from typing import Optional, Union

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from lowerpines.bot import Bot as LPBot
from lowerpines.gmi import GMI
from lowerpines.message import ComplexMessage
from lowerpines.message import Message

from saucerbot.groupme.handlers import registry
from saucerbot.utils import get_tasted_brews

logger = logging.getLogger(__name__)


@lru_cache()
def get_gmi(access_token: str) -> GMI:
    return GMI(access_token)


class UserInfoManager(models.Manager):

    def from_token(self, access_token):
        gmi = get_gmi(access_token)
        return super().create(access_token=access_token, user_id=gmi.user.get().user_id)


class UserInfo(models.Model):
    access_token: str = models.CharField(max_length=64, unique=True)
    user_id: str = models.CharField(max_length=32, unique=True)

    objects = UserInfoManager()

    def is_valid(self):
        return bool(self.access_token)

    @property
    def gmi(self):
        return get_gmi(self.access_token)


class BotManager(models.Manager):

    def create(self, **kwargs):
        user_info = kwargs.get('user_info')
        name = kwargs.get('name')
        slug = kwargs.get('slug')

        if user_info and name and slug and 'group' in kwargs:
            group = kwargs.pop('group')
            callback_url = 'https://{}{}'.format(
                settings.SERVER_DOMAIN,
                reverse('groupme:bot-callback', kwargs={'slug': slug}),
            )
            bot = user_info.gmi.bots.create(group, name, callback_url,
                                            kwargs.pop('avatar_url'))
            kwargs['bot_id'] = bot.bot_id

        return super().create(**kwargs)


class Bot(models.Model):
    bot_id: str = models.CharField(max_length=32)
    name: str = models.CharField(max_length=64)
    slug: str = models.CharField(max_length=64, unique=True)
    user_info: UserInfo = models.ForeignKey(UserInfo, models.CASCADE, related_name='bots')

    objects = BotManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bot: Optional[LPBot] = None

    def __str__(self):
        return f'{self.name} (slug={self.slug})'

    def __repr__(self):
        return f'Bot({self.bot_id}, {self.name}, {self.slug}, {self.user_info_id})'

    @property
    def bot(self) -> LPBot:
        if not self._bot:
            self._bot = self.user_info.gmi.bots.get(bot_id=self.bot_id)  # pylint: disable=no-member
        return self._bot

    def post_message(self, message: Union[str, ComplexMessage]) -> None:
        self.bot.post(message)

    def handle_message(self, message: Message) -> bool:
        # We don't want to accidentally respond to ourself
        if message.sender_type == 'bot' and self.name in message.name:
            return False

        handler_names = [h.handler_name for h in self.handlers.all()]

        for handler in registry:
            if handler.name not in handler_names:
                continue

            logger.debug(f"Trying message handler {handler.name} ...")

            if handler.regexes:
                # This is a regex handler, special case
                for regex in handler.regexes:
                    match = regex.search(message.text)
                    if match:
                        # We matched!  Now call our handler and break out of the loop

                        # We want to see what arguments our function takes, though.
                        sig = inspect.signature(handler.func)

                        kwargs = {}
                        if 'message' in sig.parameters:
                            kwargs['message'] = message
                        if 'match' in sig.parameters:
                            kwargs['match'] = match

                        handler.func(self.bot, **kwargs)
                        return True
            else:
                # Just a plain handler.
                # If it returns something truthy, it matched, so it means we should stop
                if handler.func(self.bot, message):
                    return True

        return False


@receiver(pre_delete, sender=Bot)
def delete_bot(sender, instance: Bot, **kwargs):  # pylint: disable=unused-argument
    instance.bot.delete()


class Handler(models.Model):
    bot: Bot = models.ForeignKey(Bot, models.CASCADE, related_name='handlers')
    handler_name: str = models.CharField(max_length=64)

    def __str__(self):
        return f'{self.bot_id} - {self.handler_name}'

    def __repr__(self):
        return f'Handler({self.bot_id}, {self.handler_name})'


class SaucerUser(models.Model):
    groupme_id: str = models.CharField(max_length=32, unique=True)
    saucer_id: str = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f'{self.saucer_id} - {self.groupme_id}'

    def __repr__(self):
        return f'SaucerUser({self.groupme_id}, {self.saucer_id})'

    def get_brews(self):
        return get_tasted_brews(self.saucer_id)


class HistoricalNickname(models.Model):
    group_id: str = models.CharField(max_length=32)
    groupme_id: str = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    nickname: str = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.nickname} - {self.timestamp}'

    def __repr__(self):
        return f'HistoricalNickname({self.groupme_id}, {self.timestamp}, {self.nickname})'
