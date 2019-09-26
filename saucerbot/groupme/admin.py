# -*- coding: utf-8 -*-

from django.contrib import admin

from saucerbot.groupme import models

admin.site.register(models.User)
admin.site.register(models.Bot)
admin.site.register(models.Handler)
admin.site.register(models.HistoricalNickname)
admin.site.register(models.SaucerUser)
