# -*- coding: utf-8 -*-

import logging
import os

from django.core.management.base import BaseCommand, CommandParser

from saucerbot.groupme.utils import get_gmi

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Helper commands to get PR deploys working"

    def add_arguments(self, parser: CommandParser):
        subparsers = parser.add_subparsers(dest='subcommand', title='subcommands')
        subparsers.required = True
        create = subparsers.add_parser('create', cmd=self)
        destroy = subparsers.add_parser('destroy', cmd=self)

    def handle(self, *args, **options) -> None:
        if options['subcommand'] == 'create':
            self.create()
        elif options['subcommand'] == 'destroy':
            self.destroy()

    def create(self) -> None:
        group = get_gmi().groups.get(group_id=os.environ['GROUPME_GROUP_ID'])

        app_name = os.environ['HEROKU_APP_NAME']

        new_bot = get_gmi().bots.create(
            group,
            app_name,
            callback_url=f'https://{app_name}.herokuapp.com/groupme/callbacks/{app_name}/',
        )

        logger.info("Created bot with ID: {}".format(new_bot.bot_id))

    def destroy(self) -> None:
        app_name = os.environ['HEROKU_APP_NAME']

        for bot in get_gmi().bots:
            if bot.name == app_name:
                logger.info(f"Destroying bot: {bot.name} <{bot.bot_id}>")
                bot.delete()
