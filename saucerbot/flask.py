# -*- coding: utf-8 -*-

import os
import re
from collections import namedtuple

from flask import Flask

from saucerbot import groupme

BOT_ID = os.environ['GROUPME_BOT_ID']


Handler = namedtuple('Handler', ['re', 'type', 'func', 'case_sensitive', 'short_circuit'])


class SaucerFlask(Flask):

    def __init__(self, *args, **kwargs):
        super(SaucerFlask, self).__init__(*args, **kwargs)
        self.handlers = []

        # Find our bot object
        self.bot = groupme.Bot.get(BOT_ID)

        # Load the group too
        self.group = groupme.Group.get(self.bot.group_id)

    def handler(self, regex=None, regex_type='search', case_sensitive=False, short_circuit=False):
        """
        Add a message handler
        """
        def wrapper(func):
            self.handlers.append(Handler(
                re.compile(regex) if regex else None,
                regex_type,
                func,
                case_sensitive,
                short_circuit,
            ))
            return func

        return wrapper
