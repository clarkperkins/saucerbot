# -*- coding: utf-8 -*-

import logging
from typing import Any, cast
from urllib.parse import quote

from django.conf import settings
from django.db.models import QuerySet
from django.views.generic import TemplateView
from rest_framework.viewsets import ReadOnlyModelViewSet

from saucerbot.core.serializers import HandlerSerializer
from saucerbot.discord.utils import get_redirect_uri
from saucerbot.handlers import registry

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "saucerbot/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["discord_auth_url"] = (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={settings.DISCORD_CLIENT_ID}"
            f"&permissions=0"
            f"&redirect_uri={quote(get_redirect_uri())}"
            f"&scope=bot%20applications.commands"
        )
        return context


class HandlerViewSet(ReadOnlyModelViewSet):
    queryset = cast(QuerySet, registry)
    serializer_class = HandlerSerializer
    lookup_field = "name"
    lookup_value_type = "str"
