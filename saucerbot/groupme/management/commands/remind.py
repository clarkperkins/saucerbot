# -*- coding: utf-8 -*-

import logging
from typing import Optional, Union

import arrow
from django.core.management.base import BaseCommand, CommandParser
from lowerpines.endpoints.message import Message
from lowerpines.message import ComplexMessage, RefAttach

from saucerbot.groupme.models import Bot
from saucerbot.utils.bridgestone import create_message, get_todays_events

logger = logging.getLogger(__name__)

LIKE_IF_POST = "Saucer at 7PM. Like if."


class Command(BaseCommand):
    help = "Commands for sending reminders"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bot: Optional[Bot] = None

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("bot", help="The name of the bot to post as")
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            help="Forces saucerbot to send a reminder on non-mondays",
        )
        subparsers = parser.add_subparsers(dest="subcommand", title="subcommands")
        subparsers.required = True
        subparsers.add_parser("like-if", help="Remind everyone to come to saucer.")
        subparsers.add_parser("whos-coming", help="Let everyone know who's coming.")

    @property
    def bot(self) -> Bot:
        if self._bot is None:
            raise ValueError("Bot was not initialized")
        return self._bot

    def handle(self, *args, **options) -> None:
        today = arrow.now("US/Central")

        if today.weekday() != 0 and not options["force"]:
            self.stdout.write("No reminders sent, it's not Monday!")
            return

        self._bot = Bot.objects.get(slug=options["bot"])

        if options["subcommand"] == "like-if":
            self.like_if()
        elif options["subcommand"] == "whos-coming":
            self.whos_coming()

    def like_if(self) -> None:
        """
        Remind everyone to come to saucer.
        """
        self.bot.post_message(LIKE_IF_POST)
        logger.info("Successfully sent reminder message.")

        todays_events = get_todays_events()
        if todays_events:
            self.bot.post_message(create_message(todays_events[0]))

    def whos_coming(self) -> None:
        """
        Let everyone know who's coming
        """
        # Since the bot post response is empty, search through the old posts to
        # find the most recent one matching the text
        for message in self.bot.bot.group.messages.recent():
            if message.text == LIKE_IF_POST and message.name == self.bot.name:
                num_likes = len(message.favorited_by)

                self.whos_coming_message(num_likes)

                if num_likes > 0:
                    self.save_seats_message(message)

                logger.info("Successfully sent reminder message.")

                # We sent a message already, don't send another
                break

    def whos_coming_message(self, num_likes: int):
        if num_likes == 0:
            phrase = "nobody is"
            ending = " 😭"
        elif num_likes == 1:
            phrase = "only 1 person is"
            ending = " 😢"
        else:
            phrase = f"{num_likes} people are"
            ending = ""

        self.bot.post_message(f"Looks like {phrase} coming tonight.{ending}")

    def save_seats_message(self, message: Message):
        user_id_map = {m.user_id: m.nickname for m in self.bot.bot.group.members}

        attachments: list[RefAttach] = []
        for user_id in message.favorited_by:
            if user_id in user_id_map:
                attachments.append(RefAttach(user_id, f"@{user_id_map[user_id]}"))

        if attachments:
            mes: Union[str, ComplexMessage] = "Save seats for:"
            for att in attachments:
                mes = mes + "\n  " + att
            self.bot.post_message(mes)
