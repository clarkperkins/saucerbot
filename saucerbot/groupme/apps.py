# -*- coding: utf-8 -*-

import logging
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings

from saucerbot.groupme.handlers import registry

logger = logging.getLogger(__name__)


class GroupMeConfig(AppConfig):
    name = "saucerbot.groupme"
    verbose_name = "GroupMe"

    def ready(self):
        # Import the handler modules
        for handler_module in settings.HANDLER_MODULES:
            start_handlers = len(registry)
            import_module(handler_module)
            logger.info(
                "Loaded %s handlers from %s",
                len(registry) - start_handlers,
                handler_module,
            )

        logger.info("Loaded %s total handlers", len(registry))
