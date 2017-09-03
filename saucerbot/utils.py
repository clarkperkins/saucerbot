# -*- coding: utf-8 -*-

import datetime
import logging
import os

from elasticsearch import Elasticsearch
import requests

from saucerbot.parsers import NewArrivalsParser

BREWS_URL = 'https://www.beerknurd.com/api/brew/list/13886'
API_URL = 'https://api.groupme.com/v3'
BOT_ID = os.environ['BOT_ID']
EMOJI_PLACEHOLDER = '\ufffd'

logger = logging.getLogger(__name__)


def load_beers_into_es():
    es = Elasticsearch(os.environ['BONSAI_URL'])

    # Make sure the template is there
    es.indices.put_template(
        'beers',
        {
            'template': 'beers-*',
            'mappings': {
                'beer': {
                    'properties': {
                        'name': {'type': 'text'},
                        'store_id': {'type': 'keyword'},
                        'brewer': {'type': 'text'},
                        'city': {'type': 'text'},
                        'country': {'type': 'text'},
                        'container': {'type': 'keyword'},
                        'style': {'type': 'text'},
                        'description': {'type': 'text'},
                        'stars': {'type': 'long'},
                        'reviews': {'type': 'long'},
                    }
                }
            }
        }
    )

    beers = requests.get(BREWS_URL).json()

    now = datetime.datetime.today()

    index_name = 'beers-nashville-{}'.format(now.strftime('%Y%m%d-%H%M%S'))

    # Manually create the index
    es.indices.create(index_name)

    # index all the beers
    for beer in beers:
        beer_id = beer.pop('brew_id')
        beer['reviews'] = int(beer['reviews'])
        if not beer['city']:
            beer.pop('city')
        if not beer['country']:
            beer.pop('country')
        es.index(index_name, 'beer', beer, beer_id)

    alias_actions = []

    # Remove old indices
    if es.indices.exists_alias(name='beers-nashville'):
        old_indices = es.indices.get_alias(name='beers-nashville')
        for index in old_indices:
            alias_actions.append({
                'remove_index': {'index': index},
            })

    # Add the new index
    alias_actions.append({
        'add': {'index': index_name, 'alias': 'beers-nashville'},
    })

    # Perform the update
    es.indices.update_aliases({'actions': alias_actions})


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
