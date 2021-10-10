# -*- coding: utf-8 -*-

import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class SaucerbotUserAuthentication(SessionAuthentication, metaclass=ABCMeta):
    @abstractmethod
    def get_user(self, request: Request):
        raise NotImplementedError()

    def authenticate(
        self, request: Request
    ) -> Optional[tuple[Optional[Any], Optional[Any]]]:
        user = self.get_user(request)

        if not user:
            return None

        self.enforce_csrf(request)

        # CSRF passed with session token
        return user, None
