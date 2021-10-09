# -*- coding: utf-8 -*-

import os

import django
import rollbar
from django.conf import settings

from saucerbot.discord.client import SaucerbotClient


def main():
    django.setup()

    rollbar_access_token = os.environ.get("ROLLBAR_ACCESS_TOKEN")

    if rollbar_access_token:
        rollbar.init(
            rollbar_access_token,
            f"{os.environ['DJANGO_ENV']}-worker",
            root=settings.BASE_DIR,
        )

    client = SaucerbotClient()
    client.run(settings.DISCORD_BOT_TOKEN)
