# -*- coding: utf-8 -*-

import logging
import random
from typing import List, Union

from lowerpines.endpoints.bot import Bot
from lowerpines.endpoints.message import Message
from lowerpines.message import ComplexMessage, RefAttach

from saucerbot.groupme.handlers import registry
from saucerbot.groupme.models import SaucerUser
from saucerbot.utils import (
    brew_searcher,
    get_insult,
    get_tasted_brews,
    get_new_arrivals,
)

logger = logging.getLogger(__name__)

SHAINA_USER_ID = '6830949'

SAUCERBOT_MESSAGE_LIST: List[Union[ComplexMessage, str]] = [
    "Shut up, ",
    "Go away, ",
    "Go find your own name, ",
    "Stop being an asshole, ",
    ComplexMessage('https://media.giphy.com/media/IxmzjBNRGKy8U/giphy.gif'),
    'random',
]


@registry.handler()
def user_named_saucerbot(bot: Bot, message: Message, force_random: bool = False) -> bool:
    if message.name != 'saucerbot':
        return False

    # Send something dumb
    user_attach = RefAttach(message.user_id, f'@{message.name}')

    msg = random.choice(SAUCERBOT_MESSAGE_LIST)

    if force_random or msg == 'random':
        insult = get_insult()
        prefix = "Stop being a"
        if insult[0].lower() in ['a', 'e', 'i', 'o', 'u']:
            prefix = prefix + 'n'

        msg = prefix + ' ' + insult + ', '

    if isinstance(msg, str):
        msg = msg + user_attach

    bot.post(msg)

    return True


@registry.handler(r'my saucer id is (?P<saucer_id>[0-9]+)')
def save_saucer_id(bot: Bot, message: Message, match) -> None:
    saucer_id = match.group('saucer_id')

    tasted_beers = get_tasted_brews(saucer_id)

    if not tasted_beers:
        bot.post(f"Hmmm, it looks like {saucer_id} isn't a valid Saucer ID.")
        return

    # Otherwise it's valid.  Just update or create
    _, created = SaucerUser.objects.update_or_create(groupme_id=message.user_id,
                                                     defaults={'saucer_id': saucer_id})

    user_attach = RefAttach(message.user_id, f'@{message.name}')

    action = 'saved' if created else 'updated'

    bot.post("Thanks, " + user_attach + f"!  I {action} your Saucer ID.")


@registry.handler(r'^info (?P<search_text>.+)$')
def search_brews(bot: Bot, match) -> None:
    search_text = match.group('search_text').strip()
    bot.post(brew_searcher.brew_info(search_text))


@registry.handler([r'new beers( (?P<location>[a-z ]+))?',
                   r'new arrivals( (?P<location>[a-z ]+))?'])
def new_arrivals(bot: Bot, match) -> None:
    """
    Gets all the new arrivals
    """
    location = match.group('location') or 'Nashville'

    bot.post(get_new_arrivals(location.strip()))


@registry.handler([r'deep dish', r'thin crust'])
def pizza(bot: Bot) -> None:
    """
    complain about pizza
    """
    bot.post("That is a false binary and you know it, asshole")


@registry.handler(r'like if')
def like_if(bot: Bot) -> None:
    bot.post("Hey that's my job")


@registry.handler([r' bot ', r'zo'])
def zo_is_dead(bot: Bot) -> None:
    bot.post("Zo is dead.  Long live saucerbot.")


@registry.handler([r'pong', r'beer pong'])
def troll(bot: Bot) -> None:
    shaina = None
    for member in bot.group.members:
        if member.user_id == SHAINA_USER_ID:
            shaina = member
            break

    pre_message: Union[RefAttach, str]

    if shaina:
        pre_message = RefAttach(SHAINA_USER_ID, f'@{shaina.nickname}')
    else:
        pre_message = "Shaina"

    bot.post(pre_message + " is the troll")
