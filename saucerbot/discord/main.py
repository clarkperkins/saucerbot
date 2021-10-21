# -*- coding: utf-8 -*-

import os
from typing import Optional

import click
import django
import requests
import rollbar
from django.conf import settings


@click.group()
def main():
    """
    Main discord worker entrypoint
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
    os.environ.setdefault("DJANGO_ENV", "production")

    django.setup()


@main.command()
def run():
    # pylint: disable=import-outside-toplevel

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


@main.command()
@click.argument("guild_id", required=False)
def create_commands(guild_id: Optional[str]):
    base_url = (
        f"https://discord.com/api/v8/applications/{settings.DISCORD_APPLICATION_ID}"
    )

    if guild_id:
        url = f"{base_url}/guilds/{guild_id}/commands"
    else:
        url = f"{base_url}/commands"

    json = {
        "name": "whoami",
        "type": 1,
        "description": "List my old display names",
        "options": [],
    }

    headers = {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    r = requests.post(url, headers=headers, json=json)

    r.raise_for_status()

    click.echo("Successfully created whoami command")
