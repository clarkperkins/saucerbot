# -*- coding: utf-8 -*-


import logging
import re

import requests

from saucerbot import app, utils

CATFACTS_URL = 'https://catfact.ninja/fact'

logger = logging.getLogger(__name__)

REMOVE_RE = re.compile(r'^(?P<remover>.*) removed (?P<removee>.*) from the group\.$')
ADD_RE = re.compile(r'^(?P<adder>.*) added (?P<addee>.*) to the group\.$')
CHANGE_RE = re.compile(r'^(?P<old_name>.*) changed name to (?P<new_name>.*)$')


@app.handler()
def mars(message):
    """
    Sends a message about mars if a user posts an image
    """
    for attachment in message['attachments']:
        if attachment['type'] == 'image':
            pre_message = "That's a cool picture of Mars, "
            attachments = [
                {
                    'type': 'mentions',
                    'user_ids': [message['user_id']],
                    'loci': [(len(pre_message), len(message['name']) + 1)],
                }
            ]

            full_message = '{}@{}'.format(pre_message, message['name'])

            utils.send_message(full_message, attachments=attachments)
            break


@app.handler()
def you_suck_too_coach(message):
    """
    Sends 'YOU SUCK TOO COACH'
    """
    if 'you suck' in message['text'].lower():
        utils.send_message('YOU SUCK TOO COACH')


@app.handler()
def catfacts(message):
    """
    Sends catfacts!
    """
    if 'cat' in message['text'].lower():
        catfact = requests.get(CATFACTS_URL).json()
        utils.send_message(catfact['fact'])


@app.handler()
def new_arrivals(message):
    """
    Gets all the new arrivals
    """
    matches = ('new arrivals', 'new beers')

    for match in matches:
        if match in message['text'].lower():
            utils.send_message(utils.get_new_arrivals())
            break


@app.handler()
def vandy(message):
    """
    Vandy things
    """
    if 'go dores' in message['text'].lower():
        utils.send_message('ANCHOR DOWN \u2693\ufe0f')

    if 'anchor down' in message['text'].lower():
        utils.send_message('GO DORES')


@app.handler()
def system_messages(message):
    """
    Process system messages
    """
    if not message['system']:
        return

    remove_match = REMOVE_RE.match(message['text'])
    add_match = ADD_RE.match(message['text'])
    change_name_match = CHANGE_RE.match(message['text'])

    if remove_match:
        utils.send_message('{emoji}', attachments=[utils.get_emoji_attachment([[4, 36]])])

    if add_match:
        utils.send_message('{emoji}', attachments=[utils.get_emoji_attachment([[2, 44]])])

    if change_name_match:
        utils.send_message('{emoji}', attachments=[utils.get_emoji_attachment([[1, 81]])])


@app.handler()
def pizza(message):
    """
    complain about pizza
    """
    matches = ('thin crust', 'deep dish')

    for match in matches:
        if match in message['text'].lower():
            utils.send_message('That is a false binary and you know it, asshole')
            break
