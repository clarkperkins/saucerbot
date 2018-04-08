# -*- coding: utf-8 -*-

import logging
import re
from typing import Any, Dict, List

import arrow
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from elasticsearch import Elasticsearch, RequestError

from saucerbot.utils.parsers import NewArrivalsParser

# This url is specific to nashville
BREWS_ALIAS_NAME = 'brews-nashville'
BREWS_URL = 'https://www.beerknurd.com/api/brew/list/13886'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{}'

logger = logging.getLogger(__name__)

ABV_RE = re.compile(r'(?P<abv>[0-9]+(\.[0-9]+)?)%')


def get_es_client() -> Elasticsearch:
    return Elasticsearch(settings.ELASTICSEARCH_URL)


def get_tasted_brews(saucer_id) -> List[Dict[str, Any]]:
    r = requests.get(TASTED_URL.format(saucer_id))
    return r.json()


def load_nashville_brews() -> None:
    es = get_es_client()

    logger.info("Updating index template")

    # Make sure the template is there
    es.indices.put_template(
        'brews',
        {
            'template': 'brews-*',
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
                        'abv': {'type': 'float'},
                    }
                }
            }
        }
    )

    brews = requests.get(BREWS_URL).json()

    logger.info(f"Retrieved {len(brews)} nashville brews from beerknurd.com")

    timestamp = arrow.now('US/Central').format('YYYYMMDD-HHmmss')

    index_name = f'{BREWS_ALIAS_NAME}-{timestamp}'

    # Manually create the index
    es.indices.create(index_name)

    logger.info(f"Loading brews into {index_name}")

    # index all the brews
    for brew in brews:
        brew_id = brew.pop('brew_id')
        brew['reviews'] = int(brew['reviews'])
        if not brew['city']:
            brew.pop('city')
        if not brew['country']:
            brew.pop('country')
        abv_match = ABV_RE.search(brew['description'])
        if abv_match:
            brew['abv'] = float(abv_match.group('abv'))
        es.index(index_name, 'brew', brew, brew_id)

    alias_actions = []

    # Remove old indices
    if es.indices.exists_alias(name=BREWS_ALIAS_NAME):
        old_indices = es.indices.get_alias(name=BREWS_ALIAS_NAME)
        for index in old_indices:
            logger.info(f"Marking {index} for deletion")
            alias_actions.append({
                'remove_index': {'index': index},
            })

    logger.info(f"Adding {index_name} to the {BREWS_ALIAS_NAME} alias")
    # Add the new index
    alias_actions.append({
        'add': {'index': index_name, 'alias': BREWS_ALIAS_NAME},
    })

    # Perform the update
    try:
        es.indices.update_aliases({'actions': alias_actions})
    except RequestError:
        logger.warning("There was an error updating the indices.  "
                       "Will only add the new index & not delete old indices.")
        es.indices.put_alias(index_name, BREWS_ALIAS_NAME)

    # Grab all the matching indices
    old_indices = es.indices.get(f'{BREWS_ALIAS_NAME}-*')

    del old_indices[index_name]

    if old_indices:
        logger.info("Cleaning up old indices...")

        # Try deleting any indices that didn't already get deleted
        for old_index in old_indices:
            if old_index != index_name:
                logger.info(f"Deleting {old_index}...")
                try:
                    es.indices.delete(old_index)
                except RequestError:
                    logger.info(f"Error deleting {old_index}.  Leaving it in place.")


def get_insult() -> str:
    r = requests.get('http://www.robietherobot.com/insult-generator.htm')
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.select('center > table > tr > td > h1')[0].text.strip()


def get_new_arrivals() -> str:
    parser = NewArrivalsParser()

    beers = parser.parse()

    return '\n'.join(x['name'] for x in beers)
