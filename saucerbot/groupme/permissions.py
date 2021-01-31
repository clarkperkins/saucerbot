# -*- coding: utf-8 -*-

import logging

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from saucerbot.groupme.models import User

logger = logging.getLogger(__name__)


class HasGroupMeUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and isinstance(request.user, User))
