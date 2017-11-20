import requests
import os
import re
import logging
import random
import json
from saucerbot import app
from lowerpines.endpoints.image import ImageConvertRequest
from lowerpines.message import ImageAttach, ComplexMessage

flickr_url = 'https://api.flickr.com/services/rest/'
logger: logging.Logger = logging.getLogger(__name__)
janet_messages = [
    "I think THIS is what you're looking for!",
    "Ride or die!",
    "Here you go!",
    "Found it!"
]


def get_api_key() -> str:
    return os.getenv('FLICKR_API_KEY', None)


def unwrap_flickr_response(text: str):
    if text.startswith('jsonFlickrApi('):
        return text[len('jsonFlickrApi('): -1]
    return text


def search_flickr(terms) -> []:
    api_key = get_api_key()
    if api_key is None:
        raise EnvironmentError("Expected environment variable FLICKR_API_KEY, none found")
    args = {
        'api_key': api_key,
        'method': 'flickr.photos.search',
        'extras': 'url_m',
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


def select_url(photos) -> str:
    urls = [photo['url_m'] for photo in photos]
    return random.choice(urls)


def get_stop_words():
    saucerbot_dir = os.path.split(__file__)[0]
    stopwords = open(saucerbot_dir + '/resources/stopwords.txt', 'r')
    words = [word.strip() for word in stopwords]
    stopwords.close()
    return words


blacklist_words = get_stop_words()


def select_terms_from_message(message: str) -> list:
    alphabetic_only = re.compile('[^a-z\s]').sub('', message.lower())
    words = set(re.compile('\s+').split(alphabetic_only))
    words = [w for w in words if len(w) > 2 and w not in blacklist_words]
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

