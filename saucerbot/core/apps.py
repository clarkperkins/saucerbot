# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.conf import settings

from saucerbot.handlers import registry


class CoreConfig(AppConfig):
    name = "saucerbot.core"
    verbose_name = "Saucerbot"

    def ready(self):
        # Import the handler modules
        registry.initialize(settings.HANDLER_MODULES)
