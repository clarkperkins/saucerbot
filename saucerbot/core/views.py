# -*- coding: utf-8 -*-

import logging
from typing import cast

from django.db.models import QuerySet
from rest_framework.viewsets import ReadOnlyModelViewSet

from saucerbot.core.serializers import HandlerSerializer
from saucerbot.handlers import registry

logger = logging.getLogger(__name__)


class HandlerViewSet(ReadOnlyModelViewSet):
    queryset = cast(QuerySet, registry)
    serializer_class = HandlerSerializer
    lookup_field = "name"
    lookup_value_type = "str"
