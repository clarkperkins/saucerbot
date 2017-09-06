# -*- coding: utf-8 -*-

import os
import datetime
import logging

import click

from saucerbot.bridgestone import create_message, get_todays_events
from saucerbot import app, db, groupme, utils

logger = logging.getLogger(__name__)


LIKE_IF_POST = "Saucer at 7PM. Like if."


@app.cli.command()
def initdb():
    """
    Initializes the database.
    """
    # So the app knows about the models to create
    from saucerbot import models

    # Do the initialization
    db.create_all()
    logger.info('Initialized the database.')


@app.cli.command()
@click.option('--force', is_flag=True, help='Forces saucerbot to send a reminder on non-mondays')
def remind(force):
    """
    Remind everyone to come to saucer.
    """
    today = datetime.datetime.now()

    if today.weekday() == 0 or force:
        todays_events = get_todays_events()
        if app.bot.post(LIKE_IF_POST):
            logger.info('Successfully sent reminder message.')
        else:
            logger.warning('Failed to send reminder message')

        if len(todays_events) > 0:
            app.bot.post(create_message(todays_events[0]))
    else:
        logger.info("Not sending message, it's not Monday!")


@app.cli.command('remind-again')
def remind_again():
    """
    Sends a message with the number of people coming tonight.
    """
    # Since the bot post response is empty, search through the old posts to
    # find the most recent one matching the text
    for message in app.group.messages():
        if message.text == LIKE_IF_POST and message.name == 'saucerbot':
            num_likes = len(message.favorited_by)

            if num_likes == 0:
                phrase = 'nobody is'
            elif num_likes == 1:
                phrase = 'only 1 person is'
            else:
                phrase = '{} people are'.format(num_likes)

            app.bot.post("Looks like {} coming tonight.".format(phrase))
            break


@app.cli.command('load-beers')
def load_beers():
    """
    Load all the beers.
    """
    utils.load_beers_into_es()


@app.cli.group()
def pr():
    """
    Helper commands to get PR deploys working
    """


@pr.command()
def create():
    group = groupme.Group.get(os.environ['GROUPME_GROUP_ID'])

    app_name = os.environ['HEROKU_APP_NAME']

    new_bot = groupme.Bot.create(
        app_name,
        group,
        callback_url='https://{}.herokuapp.com/hooks/groupme/'.format(app_name),
    )

    logger.info("Created bot with ID: {}".format(new_bot.bot_id))


@pr.command()
def destroy():
    app_name = os.environ['HEROKU_APP_NAME']

    bots = groupme.Bot.list()

    for bot in bots:
        if bot.name == app_name:
            logger.info("Destroying bot: {} <{}>".format(bot.name, bot.bot_id))
            bot.destroy()
