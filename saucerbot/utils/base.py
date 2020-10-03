# -*- coding: utf-8 -*-

# Remove this disable once https://github.com/timothycrosley/isort/pull/719 is merged / released
# pylint: disable=wrong-import-order

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import arrow
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from elasticsearch import Elasticsearch, RequestError
from elasticsearch.helpers import bulk

from saucerbot.utils.parsers import NewArrivalsParser

BREWS_ALIAS_NAME = 'brews'
BREWS_URL = 'https://www.beerknurd.com/api/brew/list/{}'
TASTED_URL = 'https://www.beerknurd.com/api/tasted/list_user/{}'

TEMPLATES_DIR: Path = settings.BASE_DIR / 'saucerbot' / 'resources' / 'elasticsearch' / 'templates'

logger = logging.getLogger(__name__)

ABV_RE = re.compile(r'(?P<abv>[0-9]+(\.[0-9]+)?)%')

SAUCER_LOCATIONS = {
    'addison': '13887',
    'austin': '13889',
    'charlotte': '13888',
    'columbia': '13878',
    'cordova': '13883',
    'cypress-waters': '18686214',
    'dfw-airport': '18262641',
    'fort-worth': '13891',
    'houston': '13880',
    'kansas-city': '13892',
    'little-rock': '13885',
    'memphis': '13881',
    'nashville': '13886',
    'raleigh': '13877',
    'san-antonio': '13882',
    'sugar-land': '13879',
    'the-lake': '13884',
}


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
    abv: Optional[float] = field(default=None)

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

        timestamp = arrow.now('US/Central').format('YYYYMMDD-HHmmss-SSS')

        self.index_name = f'{BREWS_ALIAS_NAME}-{timestamp}'

    def expand_brew(self, brew: Brew):
        action = {
            'index': {
                '_index': self.index_name,
            }
        }
        raw_brew: Dict[str, Any] = asdict(brew)
        return action, raw_brew

    def update_templates(self) -> None:
        logger.info("Updating elasticsearch index templates")

        for template in TEMPLATES_DIR.iterdir():
            name, _, ext = template.name.rpartition('.')

            if ext != 'json':
                logger.warning("Located a non-json template file: %s. Ignoring.", template)
                continue

            with template.open('rt', encoding='utf8') as f:
                template_json = json.load(f)

            self.es.indices.put_template(name, template_json)

    def load_all_brews(self) -> None:
        self.update_templates()
        self.es.indices.create(self.index_name)

        # Download & load the brews
        brews = self.get_all_brews()
        logger.info("Loading brews into %s", self.index_name)
        bulk(self.es, brews, chunk_size=1000, expand_action_callback=self.expand_brew)

        # Clean things up
        self.update_alias()
        self.cleanup_old_indices()

    def get_all_brews(self) -> Iterable[Brew]:
        with requests.Session() as session:
            for location, store_id in SAUCER_LOCATIONS.items():
                yield from self.get_brews(session, location, store_id)

    @staticmethod
    def get_brews(session: requests.Session, location: str, store_id: str) -> Iterable[Brew]:
        logger.info("loading brews from %s", location)
        url = BREWS_URL.format(store_id)
        brews: List[Dict[str, Any]] = session.get(url).json()

        logger.info("Retrieved %i %s brews from beerknurd.com", len(brews), location)

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
                logger.info("Marking %s for deletion", index)
                alias_actions.append({
                    'remove_index': {'index': index},
                })

        logger.info("Adding %s to the %s alias", self.index_name, BREWS_ALIAS_NAME)
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
                logger.info("Deleting %s...", old_index)
                try:
                    self.es.indices.delete(old_index)
                except RequestError:
                    logger.info("Error deleting %s.  Leaving it in place.", old_index)


class BrewsSearchUtil:
    def __init__(self):
        self.es = Elasticsearch(settings.ELASTICSEARCH_URL)

    def brew_info(self, search_term: str) -> str:
        tokens = search_term.split()

        orig_location = 'Nashville'
        location_lower = None

        if len(tokens) > 1:
            potential_location = tokens[0].lower()
            if potential_location in SAUCER_LOCATIONS:
                location_lower = potential_location
                orig_location = tokens[0]
                search_term = ' '.join(tokens[1:])

        if location_lower is None and len(tokens) > 2:
            potential_location = f"{tokens[0]}-{tokens[1]}".lower()
            if potential_location in SAUCER_LOCATIONS:
                location_lower = potential_location
                orig_location = ' '.join(tokens[:2])
                search_term = ' '.join(tokens[2:])

        location_lower = location_lower or 'nashville'
        store_id = SAUCER_LOCATIONS[location_lower]

        response = self.es.search(index=BREWS_ALIAS_NAME, body={
            'query': {
                'bool': {
                    'must': [
                        {'match': {'name': search_term}}
                    ],
                    'filter': {
                        'term': {'store_id': store_id}
                    },
                },
            }
        })

        total_hits = response['hits']['total']['value']

        if total_hits < 1:
            return f"No beers in {orig_location} found matching '{search_term}'"

        best_match = response['hits']['hits'][0]['_source']

        message = f"{total_hits} match{'' if total_hits == 1 else 'es'} " \
                  f"found in {orig_location} for '{search_term}'\n" \
                  f"Best match is {best_match['name']}:\n"

        return message + best_match['description']


# Create a singleton instance
brew_searcher = BrewsSearchUtil()


def get_tasted_brews(saucer_id: str) -> List[Dict[str, Any]]:
    r = requests.get(TASTED_URL.format(saucer_id))
    return r.json()


def get_insult() -> str:
    r = requests.get('https://www.robietherobot.com/insult-generator.htm')
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.select('center > table > tr > td > h1')[0].text.strip()


def get_new_arrivals(location: str) -> str:
    try:
        location_string = location.lower().replace(' ', '-')
        html_provider = NewArrivalsParser.create_new_arrivals_provider(location_string)
        parser = NewArrivalsParser(html_provider)
        beers = parser.parse()
        return '\n'.join(x['name'] for x in beers)
    except requests.HTTPError:
        return f"Uh oh, looks like there's no saucer in {location}!"
