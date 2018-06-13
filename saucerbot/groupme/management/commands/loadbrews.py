# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from saucerbot.utils import BrewsLoaderUtil


class Command(BaseCommand):
    help = "Load all the brews from the Nashville Saucer"

    def handle(self, *args, **options) -> None:
        loader = BrewsLoaderUtil()
        loader.load_nashville_brews()
