# -*- coding: utf-8 -*-

import io
import json
import logging
import os
import random
import re
from typing import Dict, List, Optional

import requests
from django.conf import settings
from lowerpines.endpoints.image import ImageConvertRequest
from lowerpines.message import ImageAttach, ComplexMessage

from saucerbot.groupme.utils import get_gmi

flickr_url = 'https://api.flickr.com/services/rest/'
logger: logging.Logger = logging.getLogger(__name__)
janet_messages = [
    "I think THIS is what you're looking for!",
    "Ride or die!",
    "Here you go!",
    "Found it!"
]


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
        logger.info("Failed to search flickr: status code {}".format(resp.status_code))
        logger.debug("Response: {}".format(resp.text))
        return None
    text = unwrap_flickr_response(resp.text)
    return json.loads(text)['photos']['photo']


def select_url(photos: List[Dict]) -> str:
    urls = [photo['url_m'] for photo in photos if 'url_m' in photo]
    return random.choice(urls)


def get_stop_words() -> List[str]:
    stopwords_file = os.path.join(settings.BASE_DIR, 'saucerbot', 'resources', 'stopwords.txt')
    stopwords = io.open(stopwords_file, 'rt')
    words = [word.strip() for word in stopwords]
    stopwords.close()
    return words


blacklist_words = get_stop_words()


def select_terms_from_message(message: str) -> List[str]:
    alphabetic_only = re.compile('[^a-z\s]').sub('', message.lower())
    words = set(re.compile('\s+').split(alphabetic_only))
    words = {w for w in words if len(w) > 2 and w not in blacklist_words}
    if len(words) <= 3:
        return list(words)
    else:
        return random.sample(words, 3)


def add_to_groupme_img_service(image_url: str) -> str:
    img_data = requests.get(image_url).content
    return ImageConvertRequest(img_data, get_gmi()).result


def create_message(url: str) -> ComplexMessage:
    message = random.choice(janet_messages)
    return ImageAttach(url) + message
