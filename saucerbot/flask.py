# -*- coding: utf-8 -*-

import logging
import os
import re
from collections import namedtuple
from typing import Callable, List, Optional

from flask import Flask
from lowerpines.endpoints import bot, group
from lowerpines.exceptions import NoneFoundException, MultipleFoundException
from lowerpines.gmi import GMI, get_gmi

logger = logging.getLogger(__name__)


BOT_ID = os.environ.get('GROUPME_BOT_ID')
API_KEY = os.environ.get('GROUPME_API_KEY')


Handler = namedtuple('Handler', ['regex', 'func'])


class SaucerFlask(Flask):

    def __init__(self, *args, **kwargs) -> None:
        super(SaucerFlask, self).__init__(*args, **kwargs)
        self.handlers: List[Handler] = []

        self.gmi: GMI = get_gmi(API_KEY)

        self.bot: Optional[bot.Bot] = None
        self.group: Optional[group.Group] = None

        try:
            self.bot = self.gmi.bots.get(bot_id=BOT_ID)
            self.group = self.bot.group
        except (NoneFoundException, MultipleFoundException) as e:
            logger.debug(f"Failed to load bot:  {e}")

    def handler(self, regex: str = None, case_sensitive: bool = False) -> Callable:
        """
        Add a message handler
        """
        def wrapper(func: Callable) -> Callable:
            flags = 0

            if not case_sensitive:
                flags = flags | re.IGNORECASE

            self.handlers.append(Handler(
                re.compile(regex, flags) if regex else None,
                func,
            ))
            return func

        return wrapper
