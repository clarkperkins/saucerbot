# -*- coding: utf-8 -*-

import logging
import random
from typing import Union

from lowerpines.endpoints.bot import Bot as LPBot
from lowerpines.message import ComplexMessage, RefAttach

from saucerbot.groupme.models import GroupMeBotContext
from saucerbot.handlers import BotContext, Message, registry
from saucerbot.utils import (
    brew_searcher,
    get_insult,
    get_new_arrivals,
)

logger = logging.getLogger(__name__)

CLARK_USER_ID = "6499167"
SHAINA_USER_ID = "6830949"

SAUCERBOT_MESSAGE_LIST: list[Union[ComplexMessage, str]] = [
    "Shut up, ",
    "Go away, ",
    "Go find your own name, ",
    "Stop being an asshole, ",
    ComplexMessage("https://media.giphy.com/media/IxmzjBNRGKy8U/giphy.gif"),
    "random",
]


@registry.handler(platforms=["groupme"])
def user_named_saucerbot(
    context: BotContext, message: Message, force_random: bool = False
) -> bool:
    """
    Chastise people who make their name saucerbot
    """
    if message.user_name != "saucerbot":
        return False

    # Send something dumb
    user_attach = RefAttach(message.user_id, f"@{message.user_name}")

    msg = random.choice(SAUCERBOT_MESSAGE_LIST)

    if force_random or msg == "random":
        insult = get_insult()
        prefix = "Stop being a"
        if insult[0].lower() in ["a", "e", "i", "o", "u"]:
            prefix = prefix + "n"

        msg = prefix + " " + insult + ", "

    if isinstance(msg, str):
        msg = msg + user_attach

    context.post(msg)

    return True


@registry.handler(r"^info (?P<search_text>.+)$")
def search_brews(context: BotContext, match) -> None:
    """
    Search for beers from various saucers
    """
    search_text = match.group("search_text").strip()
    context.post(brew_searcher.brew_info(search_text))


@registry.handler(
    [r"new beers( (?P<location>[a-z ]+))?", r"new arrivals( (?P<location>[a-z ]+))?"]
)
def new_arrivals(context: BotContext, match) -> None:
    """
    Gets all the new arrivals
    """
    location = match.group("location") or "Nashville"

    context.post(get_new_arrivals(location.strip()))


@registry.handler([r"deep dish", r"thin crust"])
def pizza(context: BotContext) -> None:
    """
    Complain about pizza
    """
    context.post("That is a false binary and you know it, asshole")


@registry.handler(r"like if")
def like_if(context: BotContext) -> None:
    """
    Nobody else can use like if!
    """
    context.post("Hey that's my job")


@registry.handler([r" bot ", r"zo"])
def zo_is_dead(context: BotContext) -> None:
    """
    Zo sux
    """
    context.post("Zo is dead.  Long live saucerbot.")


@registry.handler([r"pong", r"beer pong"], platforms=["groupme"])
def troll(context: GroupMeBotContext) -> None:
    """
    LOL Shaina is the troll
    """
    shaina = get_member(context.bot, SHAINA_USER_ID)
    pre_message: Union[RefAttach, str]

    if shaina:
        pre_message = shaina
    else:
        pre_message = "Shaina"

    context.post(pre_message + " is the troll")


def get_member(bot: LPBot, member_id: str) -> Union[RefAttach, None]:
    for member in bot.group.members:
        if member.user_id == member_id:
            return RefAttach(member_id, f"@{member.nickname}")
    return None


plate_party_messages: list[str] = [
    "Yeah |, when is it???",
    "Still waiting on that date |",
    "*nudge* |",
    "Don't hold your breath, | ain't gonna schedule it soon",
    "|",
]


@registry.handler(r"plate party", platforms=["groupme"])
def plate_party(context: GroupMeBotContext):
    """
    This is to troll clark lolz but some future work could be fun on this
    """
    clark = get_member(context.bot, CLARK_USER_ID)

    if not clark:
        logger.error("Somehow clark escaped the group!!!!")
    else:
        quip = random.choice(plate_party_messages).split("|")
        context.post(quip[0] + clark + quip[1])
