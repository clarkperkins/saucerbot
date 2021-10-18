# -*- coding: utf-8 -*-

import os

import django
import rollbar
from django.conf import settings


def main():
    # pylint: disable=import-outside-toplevel

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
    os.environ.setdefault("DJANGO_ENV", "production")

    django.setup()

    rollbar_access_token = os.environ.get("ROLLBAR_ACCESS_TOKEN")

    if rollbar_access_token:
        rollbar.init(
            rollbar_access_token,
            f"{os.environ['DJANGO_ENV']}-worker",
            root=settings.BASE_DIR,
        )

    from saucerbot.discord.client import SaucerbotClient

    client = SaucerbotClient()
    client.run(settings.DISCORD_BOT_TOKEN)
