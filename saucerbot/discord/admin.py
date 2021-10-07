# -*- coding: utf-8 -*-

from django.contrib import admin

from saucerbot.discord import models

admin.site.register(models.Guild)
admin.site.register(models.Channel)
admin.site.register(models.Handler)
admin.site.register(models.HistoricalNickname)
