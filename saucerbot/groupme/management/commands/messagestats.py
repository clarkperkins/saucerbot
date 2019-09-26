# -*- coding: utf-8 -*-

from collections import defaultdict
from typing import DefaultDict, Dict

from django.core.management.base import BaseCommand, CommandParser

from saucerbot.groupme.models import Bot


class Command(BaseCommand):
    help = "Message statistics"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('bot', help='The bot to get stats for')

    def handle(self, *args, **options) -> None:
        bot = Bot.objects.get(slug=options['bot'])

        messages_by_user: DefaultDict[str, int] = defaultdict(int)
        user_id_to_user: Dict[str, str] = {}

        for m in bot.bot.group.messages.all():
            user_id_to_user.setdefault(m.user_id, m.name)
            messages_by_user[m.user_id] += 1

        for messages, user_id in reversed(sorted((b, a) for a, b in messages_by_user.items())):
            print(f'{messages} - {user_id_to_user[user_id]}')
