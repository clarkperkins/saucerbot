# -*- coding: utf-8 -*-

from django.urls import path

from saucerbot.groupme.views import GroupMeCallbacks, DoresWinCallback

urlpatterns = [
    path('callbacks/<str:name>/', GroupMeCallbacks.as_view()),
    path('dores-win/', DoresWinCallback.as_view())
]
