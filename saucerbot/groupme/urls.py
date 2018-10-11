# -*- coding: utf-8 -*-

from django.urls import path

from saucerbot.groupme.views import GroupMeCallbacks, DoresWinCallback

app_name = 'groupme'

urlpatterns = [
    path('callbacks/<str:name>/', GroupMeCallbacks.as_view(), name='callbacks'),
    path('dores-win/', DoresWinCallback.as_view(), name='dores-win'),
]
