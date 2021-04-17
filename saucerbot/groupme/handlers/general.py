# -*- coding: utf-8 -*-

import logging
import os
import random
import re
import tempfile
from pathlib import Path

import arrow
import requests
from lowerpines.endpoints.bot import Bot
from lowerpines.endpoints.message import Message
from lowerpines.message import ComplexMessage, EmojiAttach, RefAttach

from saucerbot.groupme.handlers import registry
from saucerbot.groupme.models import HistoricalNickname
from saucerbot.groupme.utils import i_barely_know_her, janet

logger = logging.getLogger(__name__)

CATFACTS_CHANCE = float(os.environ.get("CATFACTS_CHANCE", 10)) / 100.0
CATFACTS_URL = "https://catfact.ninja/fact"

REMOVE_RE = re.compile(
    r"^(?P<remover>.*) removed (?P<removed_member>.*) from the group\.$"
)
ADD_RE = re.compile(r"^(?P<adder>.*) added (?P<new_member>.*) to the group\.$")
CHANGE_RE = re.compile(r"^(?P<old_name>.*) changed name to (?P<new_name>.*)$")

PICTURE_RESPONSE_CHANCE = float(os.environ.get("PICTURE_RESPONSE_CHANCE", 15)) / 100.0
PICTURE_RESPONSES = [
    "That's a cool picture of Mars!",
    "I'm gonna make that my new phone background!",
    "NSFW.",
    "Quit using up all my data!",
    "Did you take that yourself?",
    "I think I'm in that picture!",
]

CENTRAL_TIME = "US/Central"


def nickname_entry(bot: Bot, nickname: str, timestamp: arrow.Arrow) -> None:
    # Lookup the user id
    user_id = None

    # Make sure the group is up-to-date
    bot.group.refresh()
    for member in bot.group.members:
        if member.nickname == nickname:
            user_id = member.user_id
            break

    if not user_id:
        logger.warning(
            "Failed to find user_id for %s... Could not log nickname", nickname
        )
        return

    HistoricalNickname.objects.create(
        group_id=bot.group_id,
        groupme_id=user_id,
        timestamp=timestamp.datetime,
        nickname=nickname,
    )


@registry.handler(always_run=True)
def system_messages(bot: Bot, message: Message) -> bool:
    """
    Process system messages:
    * Nickname changes
    * Added users
    * Removed users
    """
    if not message.system:
        return False

    remove_match = REMOVE_RE.match(message.text)
    add_match = ADD_RE.match(message.text)
    change_name_match = CHANGE_RE.match(message.text)

    # Grab an arrow time in UTC
    timestamp = arrow.get(message.created_at)

    if remove_match:
        bot.post(ComplexMessage([EmojiAttach(4, 36)]))
        return True

    if add_match:
        bot.post(ComplexMessage([EmojiAttach(2, 44)]))

        # Log the new member
        new_member = add_match.group("new_member")
        nickname_entry(bot, new_member, timestamp)

        return True

    if change_name_match:
        bot.post(ComplexMessage([EmojiAttach(1, 81)]))

        # Log the name change
        new_name = change_name_match.group("new_name")
        nickname_entry(bot, new_name, timestamp)

        return True

    return False


@registry.handler(r"whoami")
def whoami(bot: Bot, message: Message) -> None:
    """
    Display a user's historical nicknames
    """
    nicknames = HistoricalNickname.objects.filter(
        group_id=bot.group_id, groupme_id=message.user_id
    ).order_by("-timestamp")

    response = ""

    # We only care about central time!
    now = arrow.now(CENTRAL_TIME)

    for nickname in nicknames:
        timestamp = arrow.get(nickname.timestamp)
        next_line = f"{nickname.nickname} {timestamp.humanize(now)}\n"
        if len(response) + len(next_line) > 1000:
            bot.post(response)
            response = next_line
        else:
            response += next_line

    # make sure to post the rest at the end
    if response:
        bot.post(response)


@registry.handler()
def mars(bot: Bot, message: Message, chances: float = PICTURE_RESPONSE_CHANCE) -> bool:
    """
    Sends a message about mars if a user posts an image
    """
    for attachment in message.attachments:
        if attachment["type"] == "image" and random.random() < chances:
            user_attach = RefAttach(message.user_id, f"@{message.name}")
            response = random.choice(PICTURE_RESPONSES)
            bot.post(response[:-1] + ", " + user_attach + response[-1])
            return True

    return False


@registry.handler(r"you suck")
def you_suck_too_coach(bot: Bot) -> None:
    """
    Sends 'YOU SUCK TOO COACH'
    """
    bot.post("YOU SUCK TOO COACH")


@registry.handler(r"cat")
def catfacts(bot: Bot) -> None:
    """
    Sends catfacts!
    """
    if random.random() < CATFACTS_CHANCE:
        catfact = requests.get(CATFACTS_URL).json()
        bot.post(catfact["fact"])


@registry.handler(r"lit fam")
def lit(bot: Bot) -> None:
    """
    Battle with the lit bot
    """
    bot.post("You're not lit, I'm lit")


@registry.handler(r"@saucerbot", case_sensitive=True)
def dont_at_me(bot: Bot) -> None:
    """
    @saucerbot - Don't @ me 🙄
    """
    bot.post("don't @ me 🙄")


@registry.handler([r"@saucerbot", r"@ saucerbot"])
def sneaky(bot: Bot) -> None:
    """
    Handle other @saucerbot variants
    """
    bot.post("you think you're sneaky don't you")


@registry.handler(r"@janet")
def ask_janet(bot: Bot, message: Message) -> None:
    """
    Get images matching the text
    """
    terms = janet.select_terms_from_message(message.text)
    if not terms or random.random() < 0.125:
        terms = ["cactus"]  # CACTUS!!!
    photos = janet.search_flickr(terms)
    if not photos:
        bot.post(f"Sorry! I couldn't find anything for {terms}")
    else:
        url = janet.select_url(photos)
        groupme_image = janet.add_to_groupme_img_service(bot, url)
        bot.post(janet.create_message(groupme_image))


@registry.handler()
def handle_barely_know_her(bot: Bot, message: Message) -> bool:
    """
    I barely know her!
    """
    return i_barely_know_her(bot, message)


@registry.handler([r"69", r"sixty-nine", r"sixty nine"])
def teenage_saucerbot(bot: Bot) -> None:
    """
    69
    """
    bot.post("Nice 👌")


@registry.handler()
def too_early_for_thai(bot: Bot, message: Message) -> bool:
    """
    It's too early for thai
    """
    # Grab an arrow time in central time
    timestamp = arrow.get(message.created_at).to(CENTRAL_TIME)

    hour = timestamp.time().hour

    with Path(tempfile.gettempdir(), "thai_lock") as lockfile:
        if 3 <= hour < 8 and not lockfile.exists():
            bot.post("It's too early for thai")
            lockfile.touch()
            return True
        else:
            return False
