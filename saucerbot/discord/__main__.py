# -*- coding: utf-8 -*-
"""
Main entrypoint for discord bot. Includes django setup to make django interactions work properly.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
os.environ.setdefault("DJANGO_ENV", "production")

from saucerbot.discord.main import main

main()
