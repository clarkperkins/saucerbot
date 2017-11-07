# -*- coding: utf-8 -*-

import logging
import os
from functools import wraps
from typing import Any, Callable

import arrow
import click

from saucerbot import app, db, utils
from saucerbot.bridgestone import create_message, get_todays_events

logger = logging.getLogger(__name__)


LIKE_IF_POST = "Saucer at 7PM. Like if."


@app.cli.command()
def initdb() -> None:
    """
    Initializes the database.
    """
    # So the app knows about the models to create

    # Do the initialization
    db.create_all()
    logger.info('Initialized the database.')


@app.cli.group()
def remind() -> None:
    """
    Commands for sending reminders
    """


def only_mondays(*args, **kwargs) -> Callable:
    """
    Decorator to only send commands on mondays
    """
    def decorator(func: Callable) -> Callable:

        @click.option('--force', is_flag=True,
                      help='Forces saucerbot to send a reminder on non-mondays')
        @wraps(func)
        def wrapper(force: bool, *fargs, **fkwargs) -> Any:
            today = arrow.now('US/Central')

            # only call the function if it's a monday
            if today.weekday() == 0 or force:
                return func(*fargs, **fkwargs)
            else:
                logger.info("Not sending message, it's not Monday!")

        return wrapper

    return decorator


@remind.command('like-if')
@only_mondays()
def like_if() -> None:
    """
    Remind everyone to come to saucer.
    """
    todays_events = get_todays_events()
    if app.bot.post(LIKE_IF_POST):
        logger.info('Successfully sent reminder message.')
    else:
        logger.warning('Failed to send reminder message')

    if len(todays_events) > 0:
        app.bot.post(create_message(todays_events[0]))


@remind.command('whos-coming')
@only_mondays()
def whos_coming() -> None:
    """
    Let everyone know who's coming
    """
    # Since the bot post response is empty, search through the old posts to
    # find the most recent one matching the text
    for message in app.group.messages.recent():
        if message.text == LIKE_IF_POST and message.name == 'saucerbot':
            num_likes = len(message.favorited_by)

            if num_likes == 0:
                phrase = 'nobody is'
                ending = ' \ud83d\ude2d'
            elif num_likes == 1:
                phrase = 'only 1 person is'
                ending = ' \ud83d\ude22'
            else:
                phrase = '{} people are'.format(num_likes)
                ending = ''

            if app.bot.post("Looks like {} coming tonight.{}".format(phrase, ending)):
                logger.info('Successfully sent reminder message.')
            else:
                logger.warning('Failed to send reminder message')

            # We sent a message already, don't send another
            break


@app.cli.command('load-nashville-brews')
def load_nashville_brews() -> None:
    """
    Load all the brews from the Nashville Saucer.
    """
    utils.load_nashville_brews()


@app.cli.group()
def pr() -> None:
    """
    Helper commands to get PR deploys working
    """


@pr.command()
def create() -> None:
    group = app.gmi.groups.get(group_id=os.environ['GROUPME_GROUP_ID'])

    app_name = os.environ['HEROKU_APP_NAME']

    new_bot = app.gmi.bots.create(
        group,
        app_name,
        callback_url='https://{}.herokuapp.com/hooks/groupme/'.format(app_name),
    )

    logger.info("Created bot with ID: {}".format(new_bot.bot_id))


@pr.command()
def destroy() -> None:
    app_name = os.environ['HEROKU_APP_NAME']

    for bot in app.gmi.bots:
        if bot.name == app_name:
            logger.info("Destroying bot: {} <{}>".format(bot.name, bot.bot_id))
            bot.delete()
