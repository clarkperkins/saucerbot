# -*- coding: utf-8 -*-

from django.db import models

from saucerbot.utils import get_tasted_brews


class User(models.Model):
    groupme_id = models.CharField(max_length=32, unique=True)
    saucer_id = models.CharField(max_length=32, unique=True)

    def get_brews(self):
        return get_tasted_brews(self.saucer_id)
