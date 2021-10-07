# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request

from saucerbot.discord.models import get_user

logger = logging.getLogger(__name__)


class DiscordUserAuthentication(SessionAuthentication):
    def authenticate(
        self, request: Request
    ) -> Optional[tuple[Optional[Any], Optional[Any]]]:
        user = get_user(request)

        if not user:
            return None

        self.enforce_csrf(request)

        # CSRF passed with session token
        return user, None
