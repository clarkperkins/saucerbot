# -*- coding: utf-8 -*-

from django.contrib.auth.views import LogoutView
from django.urls import path, include

from saucerbot.groupme.routers import PathRouter
from saucerbot.groupme.views import (
    LoginRedirectView, OAuthView, BotViewSet, BotActionsViewSet, HandlerViewSet
)

app_name = 'groupme'

router = PathRouter()
router.register('bots', BotViewSet, basename='bot')
router.register('bots', BotActionsViewSet, basename='bot')
router.register('handlers', HandlerViewSet, basename='handler')

urlpatterns = [
    path('login/', LoginRedirectView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('oauth/', OAuthView.as_view(), name='oauth'),
    path('api/', include(router.urls)),
]
