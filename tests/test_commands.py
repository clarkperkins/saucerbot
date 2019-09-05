# -*- coding: utf-8 -*-

import logging

import requests_mock
from django.core.management import execute_from_command_line

logger = logging.getLogger(__name__)

GROUPME_API_URL = 'https://api.groupme.com/v3'


def ensure_post(data, ret):
    def callback(request, context):
        assert request.json() == data

        return ret

    return callback


def test_like_if(bot):
    with requests_mock.Mocker() as m:
        expected = {
            'bot_id': bot.bot_id,
            'text': "Saucer at 7PM. Like if.",
            'attachments': [],
        }

        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))
        m.get('https://www.bridgestonearena.com/events')

        execute_from_command_line(['manage.py', 'remind', 'saucerbot', 'like-if'])
