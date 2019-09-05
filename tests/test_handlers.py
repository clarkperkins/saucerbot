# -*- coding: utf-8 -*-

import json
import logging

import pytest
import requests_mock
from lowerpines.endpoints.message import Message

from saucerbot.groupme.models import Bot, UserInfo

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
    from saucerbot.groupme.handlers import general

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
        m.post(GROUPME_API_URL + '/bots/post', status_code=201,
               text=ensure_post_metadata(expected, ' '))

        raw_message = get_sample_message(bot, "", [{'type': "image"}])

        ret = general.mars(bot, Message.from_json(bot.gmi, raw_message), 1)

        assert ret


def test_mars_no_message(bot):
    from saucerbot.groupme.handlers import general

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        raw_message = get_sample_message(bot, "", [])

        ret = general.mars(bot, Message.from_json(bot.gmi, raw_message), 1)

        assert not ret


@pytest.mark.django_db
def test_zo(bot, client):
    user_info = UserInfo.objects.create(access_token='123456', user_id='123456')
    bot_model = Bot.objects.create(user_info=user_info, bot_id='123456',
                                   name='saucerbot', slug='saucerbot')

    expected = {
        'bot_id': bot.bot_id,
        'text': "Zo is dead.  Long live saucerbot.",
        'attachments': [],
    }

    # Try once before the handler is registered
    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        sample_message = get_sample_message(bot, 'zo')

        ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200
        assert ret.json() == {'message_sent': False}

    # Then register & continue
    bot_model.handlers.create(handler_name='zo')

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))

        sample_message = get_sample_message(bot, 'zo')

        ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200
        assert ret.json() == {'message_sent': True}

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))

        sample_message = get_sample_message(bot, 'hey there bot hey')

        ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200
        assert ret.json() == {'message_sent': True}

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        sample_message = get_sample_message(bot, 'bot')

        ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                          data=json.dumps(sample_message))

        assert ret.status_code == 200
        assert ret.json() == {'message_sent': False}
