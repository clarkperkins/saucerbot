# -*- coding: utf-8 -*-


import logging

import requests

from saucerbot import app
from saucerbot.utils import send_message


CATFACTS_URL = 'https://catfact.ninja/fact'

logger = logging.getLogger(__name__)


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

            full_message = "{}@{}".format(pre_message, message['name'])

            send_message(full_message, attachments=attachments)
            break


@app.handler()
def you_suck_too_coach(message):
    """
    Sends 'YOU SUCK TOO COACH'
    """
    if 'you suck' in message['text'].lower():
        send_message('YOU SUCK TOO COACH')


@app.handler()
def catfacts(message):
    """
    Sends catfacts!
    """
    if 'cat' in message['text'].lower():
        catfact = requests.get(CATFACTS_URL).json()
        send_message(catfact['fact'])
