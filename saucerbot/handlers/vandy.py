# -*- coding: utf-8 -*-

import logging

from saucerbot.handlers import BotContext, registry
from saucerbot.utils import did_the_dores_win

logger = logging.getLogger(__name__)


@registry.handler([r"ohhh+", r"go dores"])
def go_dores(context: BotContext) -> None:
    """
    Posts anchor down ⚓️
    """
    context.post("ANCHOR DOWN ⚓️")


@registry.handler(r"anchor down")
def anchor_down(context: BotContext) -> None:
    """
    Posts go dores!
    """
    context.post("GO DORES")


@registry.handler(r"black")
def black(context: BotContext) -> None:
    """
    BLACK GOLD
    """
    context.post("GOLD")


@registry.handler(r"gold")
def gold(context: BotContext) -> None:
    """
    GOLD BLACK
    """
    context.post("BLACK")


@registry.handler([r"did the dores win", r"did vandy win"])
def dores_win(context: BotContext) -> None:
    """
    The 'dores never win RIP
    """
    result = did_the_dores_win(True, True)
    if result is None:
        context.post("I couldn't find the Vandy game 😢")
    else:
        context.post(result)
