# -*- coding: utf-8 -*-

import logging

from rest_framework.authentication import SessionAuthentication

from saucerbot.groupme.models import UserInfo

logger = logging.getLogger(__name__)

USER_INFO = 'user_info_id'


class UserInfoAuthentication(SessionAuthentication):

    def authenticate(self, request):
        user_info_id = request.session.get(USER_INFO)

        try:
            user_info = UserInfo.objects.get(id=user_info_id)
        except UserInfo.DoesNotExist:
            user_info = None

        if not user_info or not user_info.is_valid():
            return None

        self.enforce_csrf(request)

        # CSRF passed with session token
        return None, user_info
