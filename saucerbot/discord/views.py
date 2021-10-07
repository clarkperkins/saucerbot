# -*- coding: utf-8 -*-

import logging
import uuid
from urllib.parse import quote

from django.conf import settings
from django.urls import reverse
from django.views.generic import RedirectView
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import UpdateModelMixin
from rest_framework.viewsets import ReadOnlyModelViewSet

from saucerbot.discord.authentication import DiscordUserAuthentication
from saucerbot.discord.models import (
    Guild,
    User,
    InvalidDiscordUser,
    new_user,
    SESSION_KEY,
)
from saucerbot.discord.permissions import HasDiscordUser
from saucerbot.discord.serializers import ChannelSerializer, GuildSerializer
from saucerbot.discord.utils import exchange_code, get_redirect_uri

logger = logging.getLogger(__name__)

STATE_SESSION_KEY = "_discord_state"


class LoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if SESSION_KEY in self.request.session:
            return reverse("discord:api-root")
        else:
            state = str(uuid.uuid4())
            self.request.session[STATE_SESSION_KEY] = state

            return (
                f"https://discord.com/api/oauth2/authorize"
                f"?client_id={settings.DISCORD_CLIENT_ID}"
                f"&redirect_uri={quote(get_redirect_uri())}"
                f"&state={state}"
                f"&response_type=code"
                f"&scope=identify%20guilds"
                f"&prompt=consent"
            )


class OAuthView(RedirectView):
    pattern_name = "discord:guild-list"

    def get(self, request, *args, **kwargs):
        code = self.request.GET.get("code")
        state = self.request.GET.get("state")
        stored_state = self.request.session[STATE_SESSION_KEY]

        if state != stored_state:
            raise InvalidDiscordUser("State token didn't match")

        del self.request.session[STATE_SESSION_KEY]

        if code:
            token_data = exchange_code(code)
            new_user(
                self.request,
                token_data["access_token"],
                token_data["token_type"],
                token_data["refresh_token"],
                token_data["expires_in"],
            )
            return super().get(request, *args, **kwargs)
        else:
            raise InvalidDiscordUser("Missing access token")


class GuildViewSet(ReadOnlyModelViewSet):
    serializer_class = GuildSerializer
    lookup_field = "name"
    lookup_value_type = "slug"
    authentication_classes = [DiscordUserAuthentication]
    permission_classes = [HasDiscordUser]

    def get_queryset(self):
        user: User = self.request.user
        guild_ids = user.guild_ids
        return Guild.objects.filter(guild_id__in=guild_ids)


class ChannelViewSet(ReadOnlyModelViewSet, UpdateModelMixin):
    serializer_class = ChannelSerializer
    lookup_field = "name"
    lookup_value_type = "slug"
    authentication_classes = [DiscordUserAuthentication]
    permission_classes = [HasDiscordUser]

    def get_queryset(self):
        user: User = self.request.user
        guild_ids = user.guild_ids

        guild = get_object_or_404(
            Guild, name=self.kwargs["guild_name"], guild_id__in=guild_ids
        )

        return guild.channels.all().prefetch_related("handlers")
