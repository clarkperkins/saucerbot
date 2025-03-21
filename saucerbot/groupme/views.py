# -*- coding: utf-8 -*-

import json
import logging
from typing import Any

from django.conf import settings
from django.urls import reverse
from django.views.generic import RedirectView
from lowerpines.endpoints.message import Message
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from saucerbot.core.models import InvalidUser
from saucerbot.groupme.authentication import GroupMeUserAuthentication
from saucerbot.groupme.models import SESSION_KEY, Bot, new_user
from saucerbot.groupme.permissions import HasGroupMeUser
from saucerbot.groupme.serializers import BotSerializer

logger = logging.getLogger(__name__)


class LoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if SESSION_KEY in self.request.session:
            return reverse("groupme:api-root")
        else:
            return (
                "https://oauth.groupme.com/oauth/authorize"
                f"?client_id={settings.GROUPME_CLIENT_ID}"
            )


class OAuthView(RedirectView):
    pattern_name = "groupme:api-root"

    def get(self, request, *args, **kwargs):
        access_token = self.request.GET.get("access_token")

        if access_token:
            new_user(self.request, access_token)
            return super().get(request, *args, **kwargs)
        else:
            raise InvalidUser("Missing access token")


class BotViewSet(ModelViewSet):
    serializer_class = BotSerializer
    lookup_field = "slug"
    lookup_value_type = "slug"
    authentication_classes = [GroupMeUserAuthentication]
    permission_classes = [HasGroupMeUser]

    def get_queryset(self):
        return (
            Bot.objects.filter(owner=self.request.user)
            .select_related("owner")
            .prefetch_related("handlers")
        )

    def perform_create(self, serializer: BaseSerializer[Any]):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance: Bot):  # type: ignore[override]
        # Delete the bot from groupme first, then delete ours in the database
        if instance.bot:
            instance.bot.delete()
        instance.delete()


class BotActionsViewSet(GenericViewSet):
    queryset = Bot.objects.select_related("owner")
    serializer_class = BotSerializer
    lookup_field = "slug"
    lookup_value_type = "slug"
    permission_classes = [AllowAny]

    def parse_as_message(self, bot: Bot) -> Message:
        if logger.isEnabledFor(logging.INFO):
            raw_json = json.dumps(self.request.data, ensure_ascii=False)
            logger.info("Received raw message: %s", raw_json)

        # Load it as a groupme message
        try:
            return Message.from_json(bot.owner.gmi, self.request.data)
        except Exception as e:
            raise ParseError("Invalid GroupMe message") from e

    @action(methods=["POST"], detail=True)
    def callback(self, request: Request, *args, **kwargs) -> Response:
        bot: Bot = self.get_object()
        message = self.parse_as_message(bot)

        if not message:
            raise ParseError("Invalid GroupMe message")

        response = {
            "matched_handlers": bot.handle_message(message),
        }

        return Response(response)
