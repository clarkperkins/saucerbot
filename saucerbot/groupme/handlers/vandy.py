# -*- coding: utf-8 -*-

import logging

from lowerpines.endpoints.bot import Bot
from lowerpines.message import EmojiAttach

from saucerbot.groupme.handlers import registry
from saucerbot.utils import (
    did_the_dores_win,
)

logger = logging.getLogger(__name__)


@registry.handler([r'ohhh+', r'go dores'])
def go_dores(bot: Bot) -> None:
    bot.post("ANCHOR DOWN \u2693\ufe0f")


@registry.handler(r'anchor down')
def anchor_down(bot: Bot) -> None:
    bot.post("GO DORES")


@registry.handler(r'black')
def black(bot: Bot) -> None:
    bot.post("GOLD")


@registry.handler(r'gold')
def gold(bot: Bot) -> None:
    bot.post("BLACK")


@registry.handler([r'did the dores win', r'did vandy win'])
def dores_win(bot: Bot) -> None:
    result = did_the_dores_win(True, True)
    if result is None:
        bot.post("I couldn't find the Vandy game " + EmojiAttach(1, 35))
    else:
        bot.post(result)
