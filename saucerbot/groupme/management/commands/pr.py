# -*- coding: utf-8 -*-

import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from lowerpines.bot import Bot

from saucerbot.groupme.utils import get_gmi

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Helper commands to get PR deploys working"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest='subcommand', title='subcommands')
        subparsers.required = True
        subparsers.add_parser('create', cmd=self)
        subparsers.add_parser('destroy', cmd=self)

    def handle(self, *args, **options) -> None:
        if options['subcommand'] == 'create':
            self.create()
        elif options['subcommand'] == 'destroy':
            self.destroy()

    @staticmethod
    def create() -> None:
        group = get_gmi().groups.get(group_id=os.environ.get('GROUPME_GROUP_ID'))

        app_name = settings.HEROKU_APP_NAME

        new_bot: Bot = get_gmi().bots.create(
            group,
            app_name,
            callback_url=f'https://{app_name}.herokuapp.com/groupme/callbacks/{app_name}/',
        )

        logger.info(f"Created bot with ID: {new_bot.bot_id}")

    @staticmethod
    def destroy() -> None:
        app_name = settings.HEROKU_APP_NAME

        for bot in get_gmi().bots:
            if bot.name == app_name:
                logger.info(f"Destroying bot: {bot.name} <{bot.bot_id}>")
                bot.delete()
