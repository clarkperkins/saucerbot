# -*- coding: utf-8 -*-

from django.urls import path, include

from saucerbot.core.routers import PathRouter
from saucerbot.core.views import HandlerViewSet

app_name = "saucerbot"

router = PathRouter(
    extra_api_root_paths={
        "discord": "discord:api-root",
        "groupme": "groupme:api-root",
    }
)
router.register("handlers", HandlerViewSet, basename="handler")

urlpatterns = [
    path("api/", include(router.urls)),
]
