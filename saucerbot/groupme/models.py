# -*- coding: utf-8 -*-

from django.db import models

from saucerbot.utils import get_tasted_brews


class User(models.Model):
    groupme_id = models.CharField(max_length=32, unique=True)
    saucer_id = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f'{self.saucer_id} - {self.groupme_id}'

    def get_brews(self):
        return get_tasted_brews(self.saucer_id)


class HistoricalNickname(models.Model):
    groupme_id = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    nickname = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.nickname} - {self.timestamp}'
