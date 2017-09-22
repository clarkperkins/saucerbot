# -*- coding: utf-8 -*-

import os
import re
import typing
from collections import namedtuple

from flask import Flask

from saucerbot import groupme

BOT_ID = os.environ.get('GROUPME_BOT_ID')


Handler = namedtuple('Handler', ['regex', 'func'])


class SaucerFlask(Flask):

    def __init__(self, *args, **kwargs) -> None:
        super(SaucerFlask, self).__init__(*args, **kwargs)
        self.handlers: typing.List[Handler] = []

        # Find our bot object
        self.bot = groupme.Bot.get(BOT_ID)

        # Load the group too
        self.group = groupme.Group.get(self.bot.group_id) if self.bot else None

    def handler(self, regex: str = None, case_sensitive: bool = False) -> typing.Callable[[typing.Callable], typing.Callable]:
        """
        Add a message handler
        """
        def wrapper(func: typing.Callable) -> typing.Callable:
            flags = 0

            if not case_sensitive:
                flags = flags | re.IGNORECASE

            self.handlers.append(Handler(
                re.compile(regex, flags) if regex else None,
                func,
            ))
            return func

        return wrapper
