# -*- coding: utf-8 -*-

import logging

import arrow
from django.core.management.base import BaseCommand, CommandParser
from lowerpines.message import RefAttach

from saucerbot.utils.bridgestone import create_message, get_todays_events
from saucerbot.groupme.utils import get_group, post_message

logger = logging.getLogger(__name__)


LIKE_IF_POST = "Saucer at 7PM. Like if."


class Command(BaseCommand):
    help = "Commands for sending reminders"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('--force', action='store_true', dest='force',
                            help="Forces saucerbot to send a reminder on non-mondays")
        subparsers = parser.add_subparsers(dest='subcommand', title='subcommands')
        subparsers.required = True
        like_if = subparsers.add_parser('like-if', cmd=self,
                                        help="Remind everyone to come to saucer.")
        whos_coming = subparsers.add_parser('whos-coming', cmd=self,
                                            help="Let everyone know who's coming.")

    def handle(self, *args, **options) -> None:
        today = arrow.now('US/Central')

        if today.weekday() != 0 and not options['force']:
            self.stdout.write("No reminders sent, it's not Monday!")
            return

        if options['subcommand'] == 'like-if':
            self.like_if()
        elif options['subcommand'] == 'whos-coming':
            self.whos_coming()

    def like_if(self) -> None:
        """
        Remind everyone to come to saucer.
        """
        post_message(LIKE_IF_POST)
        logger.info('Successfully sent reminder message.')

        todays_events = get_todays_events()
        if todays_events:
            post_message(create_message(todays_events[0]))

    def whos_coming(self) -> None:
        """
        Let everyone know who's coming
        """
        user_id_map = {m.user_id: m.nickname for m in get_group().members}

        # Since the bot post response is empty, search through the old posts to
        # find the most recent one matching the text
        for message in get_group().messages.recent():
            if message.text == LIKE_IF_POST and message.name == 'saucerbot':
                num_likes = len(message.favorited_by)

                if num_likes == 0:
                    phrase = 'nobody is'
                    ending = ' \ud83d\ude2d'
                elif num_likes == 1:
                    phrase = 'only 1 person is'
                    ending = ' \ud83d\ude22'
                else:
                    phrase = f'{num_likes} people are'
                    ending = ''

                post_message(f"Looks like {phrase} coming tonight.{ending}")

                if num_likes > 0:
                    likes_message = 'Save seats for'
                    for user_id in message.favorited_by:
                        likes_message += ' ' + RefAttach(user_id, f'@{user_id_map[user_id]}')

                    post_message(likes_message)

                logger.info('Successfully sent reminder message.')

                # We sent a message already, don't send another
                break
