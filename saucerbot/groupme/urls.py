# -*- coding: utf-8 -*-

from django.contrib.auth.views import LogoutView
from django.urls import include, path

from saucerbot.core.routers import PathRouter
from saucerbot.groupme.authentication import GroupMeUserAuthentication
from saucerbot.groupme.views import (
    BotActionsViewSet,
    BotViewSet,
    LoginRedirectView,
    OAuthView,
)

app_name = "groupme"

router = PathRouter(
    api_root_name="GroupMe", api_root_authentication_class=GroupMeUserAuthentication
)
router.register("bots", BotViewSet, basename="bot")
router.register("bots", BotActionsViewSet, basename="bot")

urlpatterns = [
    path("groupme/login/", LoginRedirectView.as_view(), name="login"),
    path("groupme/logout/", LogoutView.as_view(), name="logout"),
    path("groupme/oauth/", OAuthView.as_view(), name="oauth"),
    path("api/groupme/", include(router.urls)),
]
