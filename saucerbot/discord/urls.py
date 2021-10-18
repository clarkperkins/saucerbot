# -*- coding: utf-8 -*-

from django.contrib.auth.views import LogoutView
from django.urls import include, path

from saucerbot.core.routers import PathRouter
from saucerbot.discord.authentication import DiscordUserAuthentication
from saucerbot.discord.views import (
    ChannelViewSet,
    GuildViewSet,
    LoginRedirectView,
    OAuthView,
)

app_name = "discord"

router = PathRouter(
    api_root_name="Discord", api_root_authentication_class=DiscordUserAuthentication
)
router.register("guilds", GuildViewSet, basename="guild")
router.register("guilds/<slug:guild_name>/channels", ChannelViewSet, basename="channel")

urlpatterns = [
    path("discord/login/", LoginRedirectView.as_view(), name="login"),
    path("discord/logout/", LogoutView.as_view(), name="logout"),
    path("discord/oauth/", OAuthView.as_view(), name="oauth"),
    path("api/discord/", include(router.urls)),
]
