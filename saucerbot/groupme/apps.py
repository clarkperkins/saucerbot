# -*- coding: utf-8 -*-

from django.apps import AppConfig


class GroupMeConfig(AppConfig):
    name = 'saucerbot.groupme'
    verbose_name = 'GroupMe'

    def ready(self):
        # Import these so they get registered
        # pylint: disable=unused-import
        import saucerbot.groupme.handlers.saucer
        import saucerbot.groupme.handlers.vandy
        import saucerbot.groupme.handlers.general
