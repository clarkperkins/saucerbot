# -*- coding: utf-8 -*-

import io
import json
import logging
import os
import re
from typing import Any, Dict, Iterable, List, Optional

import arrow
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from elasticsearch import Elasticsearch, RequestError
from elasticsearch.helpers import bulk

from saucerbot.utils.parsers import NewArrivalsParser

# This url is specific to nashville
BREWS_ALIAS_NAME = 'brews-nashville'
BREWS_URL = 'https://www.beerknurd.com/api/brew/list/13886'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{}'

logger = logging.getLogger(__name__)

ABV_RE = re.compile(r'(?P<abv>[0-9]+(\.[0-9]+)?)%')


__global_es_clients: Dict[str, Elasticsearch] = {}


def get_es_client() -> Elasticsearch:
    es_url = settings.ELASTICSEARCH_URL

    if es_url not in __global_es_clients:
        __global_es_clients[es_url] = Elasticsearch(es_url)

    return __global_es_clients[es_url]


def get_tasted_brews(saucer_id) -> List[Dict[str, Any]]:
    r = requests.get(TASTED_URL.format(saucer_id))
    return r.json()


def update_templates() -> None:
    logger.info("Updating elasticsearch index templates")

    templates_dir = os.path.join(settings.BASE_DIR, 'saucerbot',
                                 'resources', 'elasticsearch', 'templates')

    es = get_es_client()

    for template in os.listdir(templates_dir):
        name, _, ext = template.rpartition('.')

        if ext != 'json':
            logger.warning(f"Located a non-json template file: {template}. Ignoring.")
            continue

        with io.open(os.path.join(templates_dir, template), 'rt') as f:
            template_json = json.load(f)

        es.indices.put_template(name, template_json)


def get_nashville_brews(index_name: str) -> Iterable[Dict[str, Any]]:
    brews = requests.get(BREWS_URL).json()

    logger.info(f"Retrieved {len(brews)} nashville brews from beerknurd.com")

    # generator of all the brews
    def gen():
        for brew in brews:
            brew_id = brew.pop('brew_id')
            brew['reviews'] = int(brew['reviews'])
            if not brew['city']:
                brew.pop('city')
            if not brew['country']:
                brew.pop('country')
            brew['description'] = brew['description'].strip()
            if brew['description'].startswith('<p>'):
                brew['description'] = brew['description'][3:]
            if brew['description'].endswith('</p>'):
                brew['description'] = brew['description'][:-4]
            abv_match = ABV_RE.search(brew['description'])
            if abv_match:
                brew['abv'] = float(abv_match.group('abv'))

            yield {
                '_index': index_name,
                '_type': 'brew',
                '_id': brew_id,
                '_source': brew,
            }

    return gen()


def load_nashville_brews() -> None:
    es = get_es_client()

    update_templates()

    timestamp = arrow.now('US/Central').format('YYYYMMDD-HHmmss')

    index_name = f'{BREWS_ALIAS_NAME}-{timestamp}'

    # Manually create the index
    es.indices.create(index_name)

    # Download & load the brews
    brews = get_nashville_brews(index_name)
    logger.info(f"Loading brews into {index_name}")
    bulk(es, brews)

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


def brew_info(search_term: str) -> str:
    es = get_es_client()

    response = es.search(BREWS_ALIAS_NAME, body={
        'query': {
            'match': {
                'name': search_term
            }
        }
    })

    total_hits = response['hits']['total']

    if total_hits < 1:
        return f"No beers found matching '{search_term}'"

    best_match = response['hits']['hits'][0]['_source']

    message = f"{total_hits} match{'' if total_hits == 1 else 'es'} found for '{search_term}'\n" \
              f"Best match is {best_match['name']}:\n"

    return message + best_match['description']


def get_insult() -> str:
    r = requests.get('http://www.robietherobot.com/insult-generator.htm')
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.select('center > table > tr > td > h1')[0].text.strip()


def get_new_arrivals() -> str:
    parser = NewArrivalsParser()

    beers = parser.parse()

    return '\n'.join(x['name'] for x in beers)
