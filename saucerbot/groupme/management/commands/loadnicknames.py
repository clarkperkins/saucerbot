# -*- coding: utf-8 -*-

import arrow
from django.core.management.base import BaseCommand

from saucerbot.groupme.models import Bot, HistoricalNickname


class Command(BaseCommand):
    help = "Load all nicknames into the database"

    def handle(self, *args, **options) -> None:
        timestamp = arrow.utcnow()

        nickname_list = []

        for bot in Bot.objects.all():
            for member in bot.group.members:
                nickname_list.append(
                    HistoricalNickname(
                        groupme_id=member.user_id,
                        timestamp=timestamp.datetime,
                        nickname=member.nickname,
                    )
                )

        HistoricalNickname.objects.bulk_create(nickname_list)
