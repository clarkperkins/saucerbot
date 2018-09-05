# -*- coding: utf-8 -*-

# Remove this disable once https://github.com/timothycrosley/isort/pull/719 is merged / released
# pylint: disable=wrong-import-order

import io
import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
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


@dataclass
class Brew:
    brew_id: str
    name: str
    store_id: str
    brewer: str
    city: Optional[str]
    country: Optional[str]
    container: str
    style: str
    description: str
    stars: int
    reviews: int
    abv: Optional[float] = field(default=None)  # type: ignore  # To be removed when mypy fixes this

    def __post_init__(self):
        if isinstance(self.stars, str):
            self.stars = int(self.stars)
        if isinstance(self.reviews, str):
            self.reviews = int(self.reviews)
        if not self.city:
            self.city = None
        if not self.country:
            self.country = None
        if not self.abv:
            # Try to pull the abv out of the description if it's not provided
            abv_match = ABV_RE.search(self.description)
            if abv_match:
                self.abv = float(abv_match.group('abv'))


class BrewsLoaderUtil:

    def __init__(self):
        self.es = Elasticsearch(settings.ELASTICSEARCH_URL)

        timestamp = arrow.now('US/Central').format('YYYYMMDD-HHmmss')

        self.index_name = f'{BREWS_ALIAS_NAME}-{timestamp}'

    def expand_brew(self, brew: Brew):
        action = {
            'index': {
                '_index': self.index_name,
                '_type': 'brew',
                '_id': brew.brew_id,
            }
        }
        raw_brew: Dict[str, Any] = asdict(brew)
        raw_brew.pop('brew_id')
        return action, raw_brew

    def update_templates(self) -> None:
        logger.info("Updating elasticsearch index templates")

        templates_dir = os.path.join(settings.BASE_DIR, 'saucerbot',
                                     'resources', 'elasticsearch', 'templates')

        for template in os.listdir(templates_dir):
            name, _, ext = template.rpartition('.')

            if ext != 'json':
                logger.warning(f"Located a non-json template file: {template}. Ignoring.")
                continue

            with io.open(os.path.join(templates_dir, template), 'rt') as f:
                template_json = json.load(f)

            self.es.indices.put_template(name, template_json)

    def load_nashville_brews(self) -> None:
        self.update_templates()
        self.es.indices.create(self.index_name)

        # Download & load the brews
        brews = self.get_nashville_brews()
        logger.info(f"Loading brews into {self.index_name}")
        bulk(self.es, brews, expand_action_callback=self.expand_brew)

        # Clean things up
        self.update_alias()
        self.cleanup_old_indices()

    @staticmethod
    def get_nashville_brews() -> Iterable[Brew]:
        brews: List[Dict[str, Any]] = requests.get(BREWS_URL).json()

        logger.info(f"Retrieved {len(brews)} nashville brews from beerknurd.com")

        for brew in brews:
            # Clean the html
            desc = BeautifulSoup(brew['description'], features='html.parser').text
            brew['description'] = desc.strip()

            yield Brew(**brew)

    def update_alias(self) -> None:
        alias_actions = []

        # Remove old indices
        if self.es.indices.exists_alias(name=BREWS_ALIAS_NAME):
            old_indices = self.es.indices.get_alias(name=BREWS_ALIAS_NAME)
            for index in old_indices:
                logger.info(f"Marking {index} for deletion")
                alias_actions.append({
                    'remove_index': {'index': index},
                })

        logger.info(f"Adding {self.index_name} to the {BREWS_ALIAS_NAME} alias")
        # Add the new index
        alias_actions.append({
            'add': {'index': self.index_name, 'alias': BREWS_ALIAS_NAME},
        })

        # Perform the update
        try:
            self.es.indices.update_aliases({'actions': alias_actions})
        except RequestError:
            logger.warning("There was an error updating the indices.  "
                           "Will only add the new index & not delete old indices.")
            self.es.indices.put_alias(self.index_name, BREWS_ALIAS_NAME)

    def cleanup_old_indices(self) -> None:
        # Grab all the matching indices
        old_indices = self.es.indices.get(f'{BREWS_ALIAS_NAME}-*')

        del old_indices[self.index_name]

        if old_indices:
            logger.info("Cleaning up old indices...")

            # Try deleting any indices that didn't already get deleted
            for old_index in old_indices:
                if old_index != self.index_name:
                    logger.info(f"Deleting {old_index}...")
                    try:
                        self.es.indices.delete(old_index)
                    except RequestError:
                        logger.info(f"Error deleting {old_index}.  Leaving it in place.")


class BrewsSearchUtil:
    def __init__(self):
        self.es = Elasticsearch(settings.ELASTICSEARCH_URL)

    def brew_info(self, search_term: str) -> str:
        response = self.es.search(BREWS_ALIAS_NAME, body={
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

        message = f"{total_hits} match{'' if total_hits == 1 else 'es'} " \
                  f"found for '{search_term}'\n" \
                  f"Best match is {best_match['name']}:\n"

        return message + best_match['description']


# Create a singleton instance
brew_searcher = BrewsSearchUtil()


def get_tasted_brews(saucer_id) -> List[Dict[str, Any]]:
    r = requests.get(TASTED_URL.format(saucer_id))
    return r.json()


def get_insult() -> str:
    r = requests.get('http://www.robietherobot.com/insult-generator.htm')
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.select('center > table > tr > td > h1')[0].text.strip()


def get_new_arrivals() -> str:
    parser = NewArrivalsParser()

    beers = parser.parse()

    return '\n'.join(x['name'] for x in beers)
