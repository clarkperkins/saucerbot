# -*- coding: utf-8 -*-

import logging
import time

import arrow
import pytest
from django.conf import settings
from django.core.management import execute_from_command_line
from elasticsearch import Elasticsearch

from saucerbot.utils.base import BREWS_ALIAS_NAME, BrewsLoaderUtil, brew_searcher

logger = logging.getLogger(__name__)


def es_assertions(es):
    assert es.indices.exists_template("brews")

    assert es.indices.exists_alias(name=BREWS_ALIAS_NAME)
    alias = es.indices.get_alias(name=BREWS_ALIAS_NAME)
    assert len(alias.keys()) == 1

    indices = es.indices.get(f"{BREWS_ALIAS_NAME}-*")
    assert len(indices.keys()) == 1

    return list(indices.keys())[0]


@pytest.mark.integration
def test_loadbrews():
    loader = BrewsLoaderUtil()
    loader.load_all_brews()

    es = Elasticsearch(settings.ELASTICSEARCH_URL)

    original_index = es_assertions(es)

    # load again and make sure we don't have double
    loader = BrewsLoaderUtil()
    loader.load_all_brews()

    new_index = es_assertions(es)

    assert new_index != original_index


@pytest.mark.integration
def test_cleanup_old():
    es = Elasticsearch(settings.ELASTICSEARCH_URL)
    timestamp = arrow.now("US/Central").format("YYYYMMDD-HHmmss-SSS")

    # Create an empty index
    es.indices.create(f"{BREWS_ALIAS_NAME}-{timestamp}")

    loader = BrewsLoaderUtil()
    loader.load_all_brews()

    es_assertions(es)


@pytest.mark.integration
def test_load_command():
    execute_from_command_line(["manage.py", "loadbrews"])

    es = Elasticsearch(settings.ELASTICSEARCH_URL)

    # Same expectations as everything else
    es_assertions(es)


@pytest.mark.integration
def test_searchbrews():
    # Make sure there's something to search
    brew_searcher.es.indices.flush("")
    time.sleep(1)

    # something that will never match
    fake_brews = brew_searcher.brew_info("asdfihasodfihasd")
    assert fake_brews == "No beers in Nashville found matching 'asdfihasodfihasd'"

    fake_brews = brew_searcher.brew_info("raleigh asdfihasodfihasd")
    assert fake_brews == "No beers in raleigh found matching 'asdfihasodfihasd'"

    fake_brews = brew_searcher.brew_info("Raleigh asdfihasodfihasd")
    assert fake_brews == "No beers in Raleigh found matching 'asdfihasodfihasd'"

    fake_brews = brew_searcher.brew_info("fort worth asdfihasodfihasd")
    assert fake_brews == "No beers in fort worth found matching 'asdfihasodfihasd'"

    # bud light is always gonna be there
    nash_brews = brew_searcher.brew_info("bud light")
    assert "found in Nashville for 'bud light'\nBest match is" in nash_brews
