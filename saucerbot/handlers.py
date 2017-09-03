# -*- coding: utf-8 -*-


import logging
import re

import requests

from saucerbot import app, utils

CATFACTS_URL = 'https://catfact.ninja/fact'

logger = logging.getLogger(__name__)

EMOJI_PLACEHOLDER = '\ufffd'

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
        rip_emoji = {
            'type': 'emoji',
            'charmap': [[4, 36]],
            'placeholder': EMOJI_PLACEHOLDER,
        }
        utils.send_message(EMOJI_PLACEHOLDER, attachments=[rip_emoji])

    if add_match:
        dog_emoji = {
            'type': 'emoji',
            'charmap': [[2, 44]],
            'placeholder': EMOJI_PLACEHOLDER,
        }
        utils.send_message(EMOJI_PLACEHOLDER, attachments=[dog_emoji])

    if change_name_match:
        sneaky_emoji = {
            'type': 'emoji',
            'charmap': [[1, 81]],
            'placeholder': EMOJI_PLACEHOLDER,
        }
        utils.send_message(EMOJI_PLACEHOLDER, attachments=[sneaky_emoji])
