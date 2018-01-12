# -*- coding: utf-8 -*-


import logging
import random
import re

import requests
from lowerpines.endpoints.message import Message
from lowerpines.message import ComplexMessage, EmojiAttach, RefAttach

from saucerbot import app, db, models, utils, the_dores

CATFACTS_URL = 'https://catfact.ninja/fact'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{user_id}'

logger: logging.Logger = logging.getLogger(__name__)

REMOVE_RE = re.compile(r'^(?P<remover>.*) removed (?P<removee>.*) from the group\.$')
ADD_RE = re.compile(r'^(?P<adder>.*) added (?P<addee>.*) to the group\.$')
CHANGE_RE = re.compile(r'^(?P<old_name>.*) changed name to (?P<new_name>.*)$')

SHAINA_USER_ID = '6830949'

SAUCERBOT_MESSAGE_LIST = [
    "Shut up, ",
    "Go away, ",
    "Go find your own name, ",
    ComplexMessage('https://media.giphy.com/media/IxmzjBNRGKy8U/giphy.gif'),
]


# Handlers run in the order they were registered

@app.handler()
def user_named_saucerbot(message: Message) -> bool:
    if message.name != 'saucerbot':
        return False

    # Send something dumb
    user_attach = RefAttach(message.user_id, f'@{message.name}')

    message = random.choice(SAUCERBOT_MESSAGE_LIST)

    if isinstance(message, str):
        message = message + user_attach

    app.bot.post(message)

    return True


@app.handler(r'my saucer id is (?P<saucer_id>[0-9]+)')
def save_saucer_id(message: Message, match) -> None:
    saucer_id = match.group('saucer_id')

    tasted_beers = utils.get_tasted_brews(saucer_id)

    if len(tasted_beers) == 0:
        app.bot.post("Hmmm, it looks like {} isn't a valid Saucer ID.".format(saucer_id))

    # Otherwise it's valid - we can move on
    user = models.User.query.filter_by(groupme_id=message.user_id).first()

    if user:
        user.saucer_id = saucer_id
    else:
        user = models.User(groupme_id=message.user_id,
                           saucer_id=saucer_id)

    db.session.add(user)
    db.session.commit()

    user_attach = RefAttach(message.user_id, f'@{message.name}')

    message = "Thanks, " + user_attach + "!  I saved your Saucer ID."

    app.bot.post(message)


@app.handler()
def mars(message: Message) -> bool:
    """
    Sends a message about mars if a user posts an image
    """
    for attachment in message.attachments:
        if attachment['type'] == 'image':
            user_attach = RefAttach(message.user_id, f'@{message.name}')

            message = "That's a cool picture of Mars, " + user_attach

            app.bot.post(message)
            return True

    return False


@app.handler(r'you suck')
def you_suck_too_coach() -> None:
    """
    Sends 'YOU SUCK TOO COACH'
    """
    app.bot.post("YOU SUCK TOO COACH")


@app.handler(r'cat')
def catfacts() -> None:
    """
    Sends catfacts!
    """
    catfact = requests.get(CATFACTS_URL).json()
    app.bot.post(catfact['fact'])


@app.handler(r'new beers')
@app.handler(r'new arrivals')
def new_arrivals() -> None:
    """
    Gets all the new arrivals
    """
    app.bot.post(utils.get_new_arrivals())


@app.handler(r'ohhh+')
@app.handler(r'go dores')
def go_dores() -> None:
    app.bot.post("ANCHOR DOWN \u2693\ufe0f")


@app.handler(r'anchor down')
def anchor_down() -> None:
    app.bot.post("GO DORES")


@app.handler(r'black')
def black() -> None:
    app.bot.post("GOLD")


@app.handler(r'gold')
def gold() -> None:
    app.bot.post("BLACK")


@app.handler()
def system_messages(message: Message) -> bool:
    """
    Process system messages
    """
    if not message.system:
        return False

    remove_match = REMOVE_RE.match(message.text)
    add_match = ADD_RE.match(message.text)
    change_name_match = CHANGE_RE.match(message.text)

    if remove_match:
        app.bot.post(ComplexMessage(EmojiAttach(4, 36)))
        return True

    if add_match:
        app.bot.post(ComplexMessage(EmojiAttach(2, 44)))
        return True

    if change_name_match:
        app.bot.post(ComplexMessage(EmojiAttach(1, 81)))
        return True

    return False


@app.handler(r'deep dish')
@app.handler(r'thin crust')
def pizza() -> None:
    """
    complain about pizza
    """
    app.bot.post("That is a false binary and you know it, asshole")


@app.handler(r'lit fam')
def lit() -> None:
    """
    battle with the lit bot
    """
    app.bot.post("You're not lit, I'm lit")


@app.handler(r'@saucerbot', case_sensitive=True)
def dont_at_me() -> None:
    app.bot.post("don't @ me \ud83d\ude44")


@app.handler(r'@saucerbot')
@app.handler(r'@ saucerbot')
def sneaky() -> None:
    app.bot.post("you think you're sneaky don't you")


@app.handler(r'like if')
def like_if() -> None:
    app.bot.post("Hey that's my job")


@app.handler(r' bot ')
@app.handler(r'zo')
def zo() -> None:
    app.bot.post("Zo is dead.  Long live saucerbot.")


@app.handler(r'pong')
@app.handler(r'beer pong')
def troll() -> None:
    shaina = None
    for member in app.group.members:
        if member.user_id == SHAINA_USER_ID:
            shaina = member
            break

    if shaina:
        pre_message = RefAttach(SHAINA_USER_ID, f'@{shaina.nickname}')
    else:
        pre_message = "Shaina"

    message = pre_message + " is the troll"
    app.bot.post(message)


@app.handler(r'did the dores win')
@app.handler(r'did vandy win')
def did_the_dores_win() -> None:
    result = the_dores.did_the_dores_win(True, True)
    if result is None:
        app.bot.post("I couldn't find the Vandy game " + EmojiAttach(1, 35))
    else:
        app.bot.post(result)
