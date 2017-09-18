# -*- coding: utf-8 -*-


import logging
import re

import requests

from saucerbot import app, db, groupme, models, utils, the_dores

CATFACTS_URL = 'https://catfact.ninja/fact'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{user_id}'

logger = logging.getLogger(__name__)

REMOVE_RE = re.compile(r'^(?P<remover>.*) removed (?P<removee>.*) from the group\.$')
ADD_RE = re.compile(r'^(?P<adder>.*) added (?P<addee>.*) to the group\.$')
CHANGE_RE = re.compile(r'^(?P<old_name>.*) changed name to (?P<new_name>.*)$')

SHAINA_USER_ID = '6830949'


# Handlers run in the order they were registered

@app.handler(r'my saucer id is (?P<saucer_id>[0-9]+)')
def save_saucer_id(message, match):
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

    pre_message = "Thanks, "
    post_message = "!  I saved your Saucer ID."
    mentions = groupme.attachments.Mentions(
        [message.user_id],
        [(len(pre_message), len(message.name) + 1)]
    )

    full_message = '{}@{}{}'.format(pre_message, message.name, post_message)

    app.bot.post(full_message, mentions)


@app.handler()
def mars(message):
    """
    Sends a message about mars if a user posts an image
    """
    for attachment in message.attachments:
        if isinstance(attachment, groupme.attachments.Image):
            pre_message = "That's a cool picture of Mars, "
            mentions = groupme.attachments.Mentions(
                [message.user_id],
                [(len(pre_message), len(message.name) + 1)]
            )

            full_message = '{}@{}'.format(pre_message, message.name)

            app.bot.post(full_message, mentions)
            return True

    return False


@app.handler(r'you suck')
def you_suck_too_coach(message, match):
    """
    Sends 'YOU SUCK TOO COACH'
    """
    app.bot.post("YOU SUCK TOO COACH")


@app.handler(r'cat')
def catfacts(message, match):
    """
    Sends catfacts!
    """
    catfact = requests.get(CATFACTS_URL).json()
    app.bot.post(catfact['fact'])


@app.handler(r'new beers')
@app.handler(r'new arrivals')
def new_arrivals(message, match):
    """
    Gets all the new arrivals
    """
    app.bot.post(utils.get_new_arrivals())


@app.handler(r'ohhh+')
@app.handler(r'go dores')
def go_dores(message, match):
    app.bot.post("ANCHOR DOWN \u2693\ufe0f")


@app.handler(r'anchor down')
def anchor_down(message, match):
    app.bot.post("GO DORES")


@app.handler(r'black')
def black(message, match):
    app.bot.post("GOLD")


@app.handler(r'gold')
def gold(message, match):
    app.bot.post("BLACK")


@app.handler()
def system_messages(message):
    """
    Process system messages
    """
    if not message.system:
        return False

    remove_match = REMOVE_RE.match(message.text)
    add_match = ADD_RE.match(message.text)
    change_name_match = CHANGE_RE.match(message.text)

    if remove_match:
        app.bot.post('{emoji}', groupme.attachments.Emoji([[4, 36]]))
        return True

    if add_match:
        app.bot.post('{emoji}', groupme.attachments.Emoji([[2, 44]]))
        return True

    if change_name_match:
        app.bot.post('{emoji}', groupme.attachments.Emoji([[1, 81]]))
        return True

    return False


@app.handler(r'deep dish')
@app.handler(r'thin crust')
def pizza(message, match):
    """
    complain about pizza
    """
    app.bot.post("That is a false binary and you know it, asshole")


@app.handler(r'lit fam')
def lit(message, match):
    """
    battle with the lit bot
    """
    app.bot.post("You're not lit, I'm lit")


@app.handler(r'@saucerbot', case_sensitive=True)
def dont_at_me(message, match):
    app.bot.post("don't @ me \ud83d\ude44")


@app.handler(r'@saucerbot')
@app.handler(r'@ saucerbot')
def sneaky(message, match):
    app.bot.post("you think you're sneaky don't you")


@app.handler(r' bot ')
@app.handler(r'zo')
def zo(message, match):
    app.bot.post("Zo is dead.  Long live saucerbot.")


@app.handler(r'pong')
@app.handler(r'beer pong')
def troll(meesage, match):
    filtered = app.group.members().filter(user_id=SHAINA_USER_ID)

    if filtered:
        shaina = filtered[0]
        mentions = groupme.attachments.Mentions(
            [SHAINA_USER_ID],
            [(0, len(shaina.nickname) + 1)]
        )

        pre_message = '@{}'.format(shaina.nickname)
        attachments = [mentions]
    else:
        pre_message = 'Shaina'
        attachments = []

    full_message = "{} is the troll".format(pre_message)
    app.bot.post(full_message, *attachments)


@app.handler(r'did the dores win')
@app.handler(r'did vandy win')
def did_the_dores_win(message, match):
    result = the_dores.did_the_dores_win(True, True)
    if result is None:
        app.bot.post("I couldn't find the Vandy game {emoji}", groupme.attachments.Emoji([[1, 35]]))
    else:
        app.bot.post(result)
