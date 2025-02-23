# -*- coding: utf-8 -*-

import logging
import os
import random
import tempfile
from pathlib import Path

import requests

from saucerbot.groupme.models import GroupMeBotContext
from saucerbot.groupme.utils import i_barely_know_her, janet
from saucerbot.handlers import BotContext, Message, registry

logger = logging.getLogger(__name__)

CATFACTS_CHANCE = float(os.environ.get("CATFACTS_CHANCE", 10)) / 100.0
CATFACTS_URL = "https://catfact.ninja/fact"

CENTRAL_TIME = "US/Central"


@registry.handler(r"you suck")
def you_suck_too_coach(context: BotContext) -> None:
    """
    Sends 'YOU SUCK TOO COACH'
    """
    context.post("YOU SUCK TOO COACH")


@registry.handler(r"cat")
def catfacts(context: BotContext) -> None:
    """
    Sends catfacts!
    """
    if random.random() < CATFACTS_CHANCE:
        catfact = requests.get(CATFACTS_URL).json()
        context.post(catfact["fact"])


@registry.handler(r"lit fam")
def lit(context: BotContext) -> None:
    """
    Battle with the lit bot
    """
    context.post("You're not lit, I'm lit")


@registry.handler(r"@saucerbot", case_sensitive=True, on_by_default=True)
def dont_at_me(context: BotContext) -> None:
    """
    @saucerbot - Don't @ me 🙄
    """
    context.post("don't @ me 🙄")


@registry.handler([r"@saucerbot", r"@ saucerbot"], on_by_default=True)
def sneaky(context: BotContext) -> None:
    """
    Handle other @saucerbot variants
    """
    context.post("you think you're sneaky don't you")


@registry.handler(r"@janet", platforms=["groupme"])
def ask_janet(context: GroupMeBotContext, message: Message) -> None:
    """
    Get images matching the text
    """
    terms = janet.select_terms_from_message(message.content)
    if not terms or random.random() < 0.125:
        terms = ["cactus"]  # CACTUS!!!
    photos = janet.search_flickr(terms)
    if not photos:
        context.post(f"Sorry! I couldn't find anything for {terms}")
    else:
        url = janet.select_url(photos)
        groupme_image = janet.add_to_groupme_img_service(context.bot, url)
        context.post(janet.create_message(groupme_image))


@registry.handler()
def handle_barely_know_her(context: BotContext, message: Message) -> bool:
    """
    I barely know her!
    """
    return i_barely_know_her(context, message)


@registry.handler([r"69", r"sixty-nine", r"sixty nine"], on_by_default=True)
def teenage_saucerbot(context: BotContext) -> None:
    """
    69
    """
    context.post("Nice 👌")


@registry.handler()
def too_early_for_thai(context: BotContext, message: Message) -> bool:
    """
    It's too early for thai
    """
    # Grab an arrow time in central time
    timestamp = message.created_at.to(CENTRAL_TIME)

    hour = timestamp.time().hour

    lockfile = Path(tempfile.gettempdir(), "thai_lock")
    if 3 <= hour < 8 and not lockfile.exists():
        context.post("It's too early for thai")
        lockfile.touch()
        return True
    else:
        return False
