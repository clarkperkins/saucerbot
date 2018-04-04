# -*- coding: utf-8 -*-

from django.db import models


class User(models.Model):
    groupme_id = models.CharField(max_length=32, unique=True)
    saucer_id = models.CharField(max_length=32, unique=True)
