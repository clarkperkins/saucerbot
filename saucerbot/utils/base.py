# -*- coding: utf-8 -*-

import logging

import requests
from bs4 import BeautifulSoup

from .http import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

INSULT_URL = "https://www.robietherobot.com/insult-generator.htm"


def get_insult() -> str | None:
    """
    Scrape an insult, or return None if the generator can't be reached or has
    changed shape.  It's a third-party page we don't control, so a failure here
    must not take the whole message callback down with it.
    """
    try:
        r = requests.get(INSULT_URL, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        logger.warning("Failed to fetch an insult", exc_info=True)
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    results = soup.select("center > table > tr > td > h1")

    if not results:
        logger.warning("Insult generator returned an unexpected page")
        return None

    return results[0].text.strip()
