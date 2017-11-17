import requests
import os
import re
import logging
import random
from saucerbot import app
from lowerpines.endpoints.image import ImageConvertRequest
from lowerpines.message import ImageAttach, ComplexMessage

flickr_url = 'https://api.flickr.com/services/rest/'
logger: logging.Logger = logging.getLogger(__name__)
janet_messages = [
    "I think THIS is what you're looking for!",
    "Ride or die!",
    "Here you go!"
]


def get_api_key() -> str:
    return os.getenv('FLICKR_API_KEY', None)


def search_flickr(terms) -> []:
    args = {
        'api_key': get_api_key(),
        'method': 'flick.photos.search',
        'extras': 'url_m',
        'text': terms,
        'format': 'json'
    }
    resp = requests.get(flickr_url, params=args)
    if resp.status_code >= 300 or resp.status_code < 200:
        logger.info("Failed to search flickr: status code {}".format(resp.status_code))
        logger.debug("Response: {}".format(resp.text))
        return None
    return resp.json()['photos']['photo']


def select_url(photos) -> str:
    urls = [photo['url_m'] for photo in photos]
    return random.choice(urls)


def sanitize_terms(terms) -> str:
    if terms is None:
        return ''
    return ''.join([i for i in str(terms) if i.isalnum()])

blacklist_words = ['find', 'for', 'get', 'janet', 'picture', 'search', 'show', 'that', 'the', 'this', 'you']


def select_terms_from_message(message: str) -> list:
    alphabetic_only = re.compile('[^a-z\w]').sub('', message.lower())
    words = set(re.compile('\w+').split(alphabetic_only))
    words = [w for w in words if w not in blacklist_words and len(w) > 2]
    if len(words) <= 3:
        return words
    else:
        return random.sample(words, 3)


def add_to_groupme_img_service(image_url: str) -> str:
    img_data = requests.get(image_url).content
    return ImageConvertRequest(img_data, app.gmi).result


def create_message(url: str) -> ComplexMessage:
    message = random.choice(janet_messages)
    return ImageAttach(url) + message

