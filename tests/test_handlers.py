# -*- coding: utf-8 -*-

import json
import logging

import requests_mock
from lowerpines.endpoints.message import Message

logger = logging.getLogger(__name__)

GROUPME_API_URL = 'https://api.groupme.com/v3'


def get_sample_message(bot, text, attachments=None):
    return {
        'attachments': attachments or [],
        'avatar_url': "https://example.com/avatar.jpeg",
        'created_at': 1507611755,
        'group_id': bot.group.group_id,
        'id': "1234567890",
        'name': "Foo Bar",
        'sender_id': "abcdef",
        'sender_type': "user",
        'source_guid': "2d01305a-da39-47f6-b293-9b6ef8708c54",
        'system': False,
        'text': text,
        'user_id': "abcdef"
    }


def ensure_post(data, ret):
    def callback(request, context):
        assert request.json() == data

        return ret

    return callback


def ensure_post_metadata(data, ret):
    def callback(request, context):
        stripped_expected = dict(data)
        stripped_actual = dict(request.json())
        del stripped_actual['text']
        for att in stripped_actual['attachments']:
            del att['loci']

        assert stripped_expected == stripped_actual
        return ret
    return callback


def fail_on_post():
    def callback(request, context):
        raise AssertionError('Request shouldn\'t have been sent!!!!')

    return callback


def test_mars(bot):
    from saucerbot.groupme import handlers

    expected = {
        'bot_id': bot.bot_id,
        'attachments': [
            {
                'type': 'mentions',
                'user_ids': ['abcdef'],
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post_metadata(expected, ' '))

        raw_message = get_sample_message(bot, "", [{'type': "image"}])

        ret = handlers.mars(Message.from_json(bot.gmi, raw_message), 1)

        assert ret


def test_mars_no_message(bot):
    from saucerbot.groupme import handlers

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        raw_message = get_sample_message(bot, "", [])

        ret = handlers.mars(Message.from_json(bot.gmi, raw_message), 1)

        assert not ret


def test_zo(bot, client):
    expected = {
        'bot_id': bot.bot_id,
        'text': "Zo is dead.  Long live saucerbot.",
        'attachments': [],
    }

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))

        sample_message = get_sample_message(bot, 'zo')

        ret = client.post('/groupme/callbacks/saucerbot/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))

        sample_message = get_sample_message(bot, 'hey there bot hey')

        ret = client.post('/groupme/callbacks/saucerbot/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        sample_message = get_sample_message(bot, 'bot')

        ret = client.post('/groupme/callbacks/saucerbot/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200

