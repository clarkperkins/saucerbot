# -*- coding: utf-8 -*-

from rest_framework.request import Request

from saucerbot.core.authentication import SaucerbotUserAuthentication
from saucerbot.discord.models import get_user


class DiscordUserAuthentication(SaucerbotUserAuthentication):
    def get_user(self, request: Request):
        return get_user(request)
