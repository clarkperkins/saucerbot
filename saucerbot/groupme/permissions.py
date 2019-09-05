# -*- coding: utf-8 -*-

import logging

from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class HasUserInfo(BasePermission):

    def has_permission(self, request, view):
        return bool(request.auth)
