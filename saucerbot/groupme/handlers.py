# -*- coding: utf-8 -*-

import logging
import os
import random
import re
from typing import Callable, List, NamedTuple, Optional, Pattern

import arrow
import requests
from lowerpines.message import ComplexMessage, EmojiAttach, Message, RefAttach

from saucerbot.groupme.models import User, HistoricalNickname
from saucerbot.groupme.utils import get_group, i_barely_know_her, janet, post_message
from saucerbot.utils import (
    brew_searcher,
    did_the_dores_win,
    get_insult,
    get_tasted_brews,
    get_new_arrivals,
)

logger = logging.getLogger(__name__)

# Some constants
CATFACTS_URL = 'https://catfact.ninja/fact'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{user_id}'

REMOVE_RE = re.compile(r'^(?P<remover>.*) removed (?P<removee>.*) from the group\.$')
ADD_RE = re.compile(r'^(?P<adder>.*) added (?P<addee>.*) to the group\.$')
CHANGE_RE = re.compile(r'^(?P<old_name>.*) changed name to (?P<new_name>.*)$')

SHAINA_USER_ID = '6830949'

SAUCERBOT_MESSAGE_LIST = [
    "Shut up, ",
    "Go away, ",
    "Go find your own name, ",
    "Stop being an asshole, ",
    ComplexMessage('https://media.giphy.com/media/IxmzjBNRGKy8U/giphy.gif'),
    'random',
]

PICTURE_RESPONSE_CHANCE = float(os.environ.get("PICTURE_RESPONSE_CHANCE", 15)) / 100.0
PICTURE_RESPONSES = [
    "That's a cool picture of Mars!",
    "I'm gonna make that my new phone background!",
    "NSFW.",
    "Quit using up all my data!",
    "Did you take that yourself?",
    "I think I'm in that picture!"
]


class Handler(NamedTuple):
    regex: Optional[Pattern[str]]
    func: Callable


class HandlerRegistry:

    def __init__(self):
        self.handlers: List[Handler] = []

    def __iter__(self):
        return iter(self.handlers)

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


# Create the registry
registry = HandlerRegistry()


# Handlers run in the order they were registered

def nickname_entry(nickname: str, timestamp: arrow.Arrow) -> None:
    # Lookup the user id
    user_id = None
    for member in get_group().members:
        if member.nickname == nickname:
            user_id = member.user_id
            break

    if not user_id:
        logger.warning(f"Failed to find user_id for {nickname}... Could not log nickname")

    HistoricalNickname.objects.create(
        groupme_id=user_id,
        timestamp=timestamp.datetime,
        nickname=nickname,
    )


@registry.handler()
def system_messages(message: Message) -> bool:
    """
    Process system messages
    """
    if not message.system:
        return False

    remove_match = REMOVE_RE.match(message.text)
    add_match = ADD_RE.match(message.text)
    change_name_match = CHANGE_RE.match(message.text)

    # Grab an arrow time in UTC
    timestamp = arrow.get(message.created_at)

    if remove_match:
        post_message(ComplexMessage(EmojiAttach(4, 36)))
        return True

    if add_match:
        post_message(ComplexMessage(EmojiAttach(2, 44)))

        # Log the new member
        new_member = add_match.group('addee')
        nickname_entry(new_member, timestamp)

        return True

    if change_name_match:
        post_message(ComplexMessage(EmojiAttach(1, 81)))

        # Log the name change
        new_name = change_name_match.group('new_name')
        nickname_entry(new_name, timestamp)

        return True

    return False


@registry.handler()
def user_named_saucerbot(message: Message) -> bool:
    if message.name != 'saucerbot':
        return False

    # Send something dumb
    user_attach = RefAttach(message.user_id, f'@{message.name}')

    message = random.choice(SAUCERBOT_MESSAGE_LIST)

    if message == 'random':
        insult = get_insult()
        prefix = "Stop being a"
        if insult[0].lower() in ['a', 'e', 'i', 'o', 'u']:
            prefix = prefix + 'n'

        message = prefix + ' ' + insult + ', '

    if isinstance(message, str):
        message = message + user_attach

    post_message(message)

    return True


@registry.handler(r'my saucer id is (?P<saucer_id>[0-9]+)')
def save_saucer_id(message: Message, match) -> None:
    saucer_id = match.group('saucer_id')

    tasted_beers = get_tasted_brews(saucer_id)

    if not tasted_beers:
        post_message(f"Hmmm, it looks like {saucer_id} isn't a valid Saucer ID.")

    # Otherwise it's valid.  Just update or create
    _, created = User.objects.update_or_create(groupme_id=message.user_id,
                                               defaults={'saucer_id': saucer_id})

    user_attach = RefAttach(message.user_id, f'@{message.name}')

    action = 'saved' if created else 'updated'
    message = "Thanks, " + user_attach + f"!  I {action} your Saucer ID."

    post_message(message)


@registry.handler(r'^info (?P<search_text>.+)$')
def search_brews(match) -> None:
    search_text = match.group('search_text').strip()
    post_message(brew_searcher.brew_info(search_text))


@registry.handler()
def mars(message: Message, chances: float = PICTURE_RESPONSE_CHANCE) -> bool:
    """
    Sends a message about mars if a user posts an image
    """
    for attachment in message.attachments:
        if attachment['type'] == 'image' and random.random() < chances:
            user_attach = RefAttach(message.user_id, f'@{message.name}')
            response = random.choice(PICTURE_RESPONSES)
            message = response[:-1] + ", " + user_attach + response[-1]
            post_message(message)
            return True

    return False


@registry.handler(r'you suck')
def you_suck_too_coach() -> None:
    """
    Sends 'YOU SUCK TOO COACH'
    """
    post_message("YOU SUCK TOO COACH")


@registry.handler(r'cat')
def catfacts() -> None:
    """
    Sends catfacts!
    """
    catfact = requests.get(CATFACTS_URL).json()
    post_message(catfact['fact'])


@registry.handler(r'new beers( (?P<location>[a-z ]+))?')
@registry.handler(r'new arrivals( (?P<location>[a-z ]+))?')
def new_arrivals(match) -> None:
    """
    Gets all the new arrivals
    """
    location = match.group('location') or 'Nashville'

    post_message(get_new_arrivals(location.strip()))


@registry.handler(r'ohhh+')
@registry.handler(r'go dores')
def go_dores() -> None:
    post_message("ANCHOR DOWN \u2693\ufe0f")


@registry.handler(r'anchor down')
def anchor_down() -> None:
    post_message("GO DORES")


@registry.handler(r'black')
def black() -> None:
    post_message("GOLD")


@registry.handler(r'gold')
def gold() -> None:
    post_message("BLACK")


@registry.handler(r'deep dish')
@registry.handler(r'thin crust')
def pizza() -> None:
    """
    complain about pizza
    """
    post_message("That is a false binary and you know it, asshole")


@registry.handler(r'lit fam')
def lit() -> None:
    """
    battle with the lit bot
    """
    post_message("You're not lit, I'm lit")


@registry.handler(r'@saucerbot', case_sensitive=True)
def dont_at_me() -> None:
    post_message("don't @ me \ud83d\ude44")


@registry.handler(r'@saucerbot')
@registry.handler(r'@ saucerbot')
def sneaky() -> None:
    post_message("you think you're sneaky don't you")


@registry.handler(r'like if')
def like_if() -> None:
    post_message("Hey that's my job")


@registry.handler(r' bot ')
@registry.handler(r'zo')
def zo() -> None:
    post_message("Zo is dead.  Long live saucerbot.")


@registry.handler(r'pong')
@registry.handler(r'beer pong')
def troll() -> None:
    shaina = None
    for member in get_group().members:
        if member.user_id == SHAINA_USER_ID:
            shaina = member
            break

    if shaina:
        pre_message = RefAttach(SHAINA_USER_ID, f'@{shaina.nickname}')
    else:
        pre_message = "Shaina"

    message = pre_message + " is the troll"
    post_message(message)


@registry.handler(r'did the dores win')
@registry.handler(r'did vandy win')
def dores_win() -> None:
    result = did_the_dores_win(True, True)
    if result is None:
        post_message("I couldn't find the Vandy game " + EmojiAttach(1, 35))
    else:
        post_message(result)


@registry.handler(r'@janet')
def ask_janet(message: Message) -> None:
    terms = janet.select_terms_from_message(message.text)
    if not terms or random.random() < 0.125:
        terms = ['cactus']  # CACTUS!!!
    photos = janet.search_flickr(terms)
    if not photos:
        post_message(f"Sorry! I couldn't find anything for {terms}")
    else:
        url = janet.select_url(photos)
        groupme_image = janet.add_to_groupme_img_service(url)
        post_message(janet.create_message(groupme_image))


@registry.handler()
def handle_barely_know_her(message: Message) -> bool:
    return i_barely_know_her(message)


@registry.handler(r'69')
@registry.handler(r'sixty-nine')
@registry.handler(r'sixty nine')
def teenage_saucerbot() -> None:
    post_message('Nice \U0001f44c')


@registry.handler(r'whoami')
def whoami(message: Message) -> None:
    nicknames = HistoricalNickname.objects.filter(groupme_id=message.user_id).order_by('-timestamp')

    response = ''

    # We only care about central time!
    now = arrow.now('US/Central')

    for nickname in nicknames:
        timestamp = arrow.get(nickname.timestamp)
        response += f'{nickname.nickname} {timestamp.humanize(now)}\n'

    if response:
        post_message(response)
