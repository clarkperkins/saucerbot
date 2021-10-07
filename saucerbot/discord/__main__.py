# -*- coding: utf-8 -*-
"""
Main entrypoint for discord bot. Includes django setup to make django interactions work properly.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
os.environ.setdefault("DJANGO_ENV", "production")
django.setup()

from django.conf import settings
from saucerbot.discord.client import SaucerbotClient

rollbar_access_token = os.environ.get("ROLLBAR_ACCESS_TOKEN")

if rollbar_access_token:
    import rollbar

    rollbar.init(
        rollbar_access_token,
        f"{os.environ['DJANGO_ENV']}-worker",
        root=settings.BASE_DIR,
    )

client = SaucerbotClient()
client.run(settings.DISCORD_BOT_TOKEN)
