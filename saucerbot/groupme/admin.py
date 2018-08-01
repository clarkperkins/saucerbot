# -*- coding: utf-8 -*-

from django.contrib import admin

from saucerbot.groupme import models

admin.site.register(models.User)
admin.site.register(models.HistoricalNickname)
