# -*- coding: utf-8 -*-

import logging

import requests
from bs4 import BeautifulSoup

from .http import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


def get_insult() -> str:
    r = requests.get(
        "https://www.robietherobot.com/insult-generator.htm",
        verify=False,
        timeout=DEFAULT_TIMEOUT,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.select("center > table > tr > td > h1")[0].text.strip()
