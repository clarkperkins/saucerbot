# -*- coding: utf-8 -*-

import logging
import os

import requests

from saucerbot.parsers import NewArrivalsParser

API_URL = 'https://api.groupme.com/v3'
BOT_ID = os.environ['BOT_ID']
EMOJI_PLACEHOLDER = '\ufffd'

logger = logging.getLogger(__name__)


def send_message(text, **kwargs):
    message = {
        'bot_id': BOT_ID,
        'text': text.format(emoji=EMOJI_PLACEHOLDER),
    }

    message.update(kwargs)

    r = requests.post('{}/bots/post'.format(API_URL), json=message)

    if r.status_code != 201:
        logger.debug('Message failed to send: {}'.format(r.text))

    return r.status_code == 201


def get_emoji_attachment(charmap):
    return {
        'type': 'emoji',
        'charmap': charmap,
        'placeholder': EMOJI_PLACEHOLDER,
    }


def get_new_arrivals():
    parser = NewArrivalsParser()

    beers = parser.parse()

    return '\n'.join(x['name'] for x in beers)
