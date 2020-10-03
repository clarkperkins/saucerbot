# -*- coding: utf-8 -*-

import json
import logging
import random
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests
from django.conf import settings
from lowerpines.endpoints.bot import Bot
from lowerpines.endpoints.image import ImageConvertRequest
from lowerpines.message import ImageAttach, ComplexMessage

flickr_url = 'https://api.flickr.com/services/rest/'
logger = logging.getLogger(__name__)
janet_messages = [
    "I think THIS is what you're looking for!",
    "Ride or die!",
    "Here you go!",
    "Found it!"
]

STOPWORDS_FILE: Path = settings.BASE_DIR / 'saucerbot' / 'resources' / 'stopwords.txt'


def unwrap_flickr_response(text: str) -> str:
    if text.startswith('jsonFlickrApi('):
        return text[len('jsonFlickrApi('): -1]
    return text


def search_flickr(terms: List[str]) -> Optional[List]:
    args = {
        'api_key': settings.FLICKR_API_KEY,
        'method': 'flickr.photos.search',
        'extras': 'url_m',
        'sort': 'relevance',
        'per_page': 40,
        'text': terms,
        'format': 'json'
    }
    resp = requests.get(flickr_url, params=args)
    if resp.status_code >= 300 or resp.status_code < 200:
        logger.info("Failed to search flickr: status code %i", resp.status_code)
        logger.debug("Response: %s", resp.text)
        return None
    text = unwrap_flickr_response(resp.text)
    return json.loads(text)['photos']['photo']


def select_url(photos: List[Dict]) -> str:
    urls = [photo['url_m'] for photo in photos if 'url_m' in photo]
    return random.choice(urls)


def get_stop_words() -> List[str]:
    with STOPWORDS_FILE.open('rt', encoding='utf8') as stopwords:
        words = [word.strip() for word in stopwords]
        return words


blacklist_words = get_stop_words()


def select_terms_from_message(message: str) -> List[str]:
    alphabetic_only = re.compile(r'[^a-z\s]').sub('', message.lower())
    words = set(re.compile(r'\s+').split(alphabetic_only))
    words = {w for w in words if len(w) > 2 and w not in blacklist_words}
    if len(words) <= 3:
        return list(words)
    else:
        return random.sample(words, 3)


def add_to_groupme_img_service(bot: Bot, image_url: str) -> str:
    img_data = requests.get(image_url).content
    return ImageConvertRequest(bot.gmi, img_data).result


def create_message(url: str) -> ComplexMessage:
    message = random.choice(janet_messages)
    return ImageAttach(url) + message
