# -*- coding: utf-8 -*-

import logging
import os
import random
import re

import arrow
from lowerpines.endpoints.bot import Bot as LPBot
from lowerpines.message import ComplexMessage, EmojiAttach, RefAttach

from saucerbot.groupme.models import (
    GroupMeBotContext,
    GroupMeMessage,
    HistoricalNickname,
)
from saucerbot.handlers import BotContext, Message, registry

logger = logging.getLogger(__name__)

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


def nickname_entry(bot: LPBot, nickname: str, timestamp: arrow.Arrow) -> None:
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


@registry.handler(always_run=True, platforms=["groupme"])
def system_messages(context: GroupMeBotContext, gmessage: GroupMeMessage) -> bool:
    """
    Process system messages:
    * Nickname changes
    * Added users
    * Removed users
    """
    message = gmessage.groupme_message

    if not message.system:
        return False

    remove_match = REMOVE_RE.match(message.text)
    add_match = ADD_RE.match(message.text)
    change_name_match = CHANGE_RE.match(message.text)

    # Grab an arrow time in UTC
    timestamp = arrow.get(message.created_at)

    if remove_match:
        context.post(ComplexMessage([EmojiAttach(4, 36)]))
        return True

    if add_match:
        context.post(ComplexMessage([EmojiAttach(2, 44)]))

        # Log the new member
        new_member = add_match.group("new_member")
        nickname_entry(context.bot, new_member, timestamp)

        return True

    if change_name_match:
        context.post(ComplexMessage([EmojiAttach(1, 81)]))

        # Log the name change
        new_name = change_name_match.group("new_name")
        nickname_entry(context.bot, new_name, timestamp)

        return True

    return False


@registry.handler(r"whoami", platforms=["groupme"])
def whoami(context: GroupMeBotContext, message: Message) -> None:
    """
    Display a user's historical nicknames
    """
    nicknames = HistoricalNickname.objects.filter(
        group_id=context.bot.group_id, groupme_id=message.user_id
    ).order_by("-timestamp")

    response = ""

    # We only care about central time!
    now = arrow.now(CENTRAL_TIME)

    for nickname in nicknames:
        timestamp = arrow.get(nickname.timestamp)
        next_line = f"{nickname.nickname} {timestamp.humanize(now)}\n"
        if len(response) + len(next_line) > 1000:
            context.post(response)
            response = next_line
        else:
            response += next_line

    # make sure to post the rest at the end
    if response:
        context.post(response)


@registry.handler(platforms=["groupme"])
def mars(
    context: BotContext,
    gmessage: GroupMeMessage,
    chances: float = PICTURE_RESPONSE_CHANCE,
) -> bool:
    """
    Sends a message about mars if a user posts an image
    """
    message = gmessage.groupme_message

    for attachment in message.attachments:
        if attachment["type"] == "image" and random.random() < chances:
            user_attach = RefAttach(message.user_id, f"@{message.name}")
            response = random.choice(PICTURE_RESPONSES)
            context.post(response[:-1] + ", " + user_attach + response[-1])
            return True

    return False
