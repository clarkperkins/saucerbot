# -*- coding: utf-8 -*-

import asyncio
import os

import click
import django
import rollbar
from django.conf import settings


@click.group()
def discord():
    """
    Main discord worker entrypoint
    """


@discord.command()
def run():
    # pylint: disable=import-outside-toplevel
    django.setup()

    rollbar_access_token = os.environ.get("ROLLBAR_ACCESS_TOKEN")

    if rollbar_access_token:
        rollbar.init(
            rollbar_access_token,
            f"{os.environ['DJANGO_ENV']}-worker",
            root=settings.BASE_DIR,
        )

    from saucerbot.discord.client import client

    client.run(settings.DISCORD_BOT_TOKEN, log_handler=None)


@discord.command()
def sync_global_commands():
    # pylint: disable=import-outside-toplevel
    from saucerbot.discord.client import client

    async def do_create():
        await client.login(settings.DISCORD_BOT_TOKEN)
        await client.tree.sync()

    asyncio.run(do_create())
