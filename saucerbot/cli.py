# -*- coding: utf-8 -*-
import os

import click

from saucerbot.discord.cli import discord

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
os.environ.setdefault("DJANGO_ENV", "production")


@click.group()
def main():
    """
    saucerbot utilities
    """


main.add_command(discord)
