# -*- coding: utf-8 -*-

from collections import defaultdict
from typing import DefaultDict, Dict

from django.core.management.base import BaseCommand

from saucerbot.groupme.utils import get_group


class Command(BaseCommand):
    help = "Message statistics"

    def handle(self, *args, **options) -> None:
        group = get_group()

        messages_by_user: DefaultDict[str, int] = defaultdict(int)
        user_id_to_user: Dict[str, str] = {}

        for m in group.messages.all():
            user_id_to_user.setdefault(m.user_id, m.name)
            messages_by_user[m.user_id] += 1

        for messages, user_id in reversed(sorted((b, a) for a, b in messages_by_user.items())):
            print(f'{messages} - {user_id_to_user[user_id]}')
