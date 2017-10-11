# -*- coding: utf-8 -*-

import logging
import requests_mock

from lowerpines.endpoints.message import Message

logger = logging.getLogger(__name__)

GROUPME_API_URL = 'https://api.groupme.com/v3'


def ensure_post(data, ret):
    def callback(request, context):
        assert request.json() == data

        return ret

    return callback


def fail_on_post():
    def callback(request, context):
        raise AssertionError('Request shouldn\'t have been sent!!!!')

    return callback


def test_mars(app):
    from saucerbot import handlers

    expected = {
        'bot_id': app.bot.bot_id,
        'text': "That's a cool picture of Mars, @Foo Bar",
        'attachments': [
            {
                'type': 'mentions',
                'loci': [[31, 8]],
                'user_ids': ['abcdef'],
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=ensure_post(expected, ' '))

        raw_message = {
            "attachments": [
                {
                    "type": "image"
                }
            ],
            "avatar_url": "https://i.groupme.com/1296x972.png.13df1c92895c4aacbf96fd6982a01aa1",
            "created_at": 1507611755,
            "group_id": app.group.group_id,
            "id": "150761175500832461",
            "name": "Foo Bar",
            "sender_id": "abcdef",
            "sender_type": "user",
            "source_guid": "2d01305a-da39-47f6-b293-9b6ef8708c54",
            "system": False,
            "text": "",
            "user_id": "abcdef"
        }

        ret = handlers.mars(Message.from_json(app.gmi, raw_message))

        assert ret


def test_mars_no_message(app):
    from saucerbot import handlers

    with requests_mock.Mocker() as m:
        m.post(GROUPME_API_URL + '/bots/post', status_code=201, text=fail_on_post())

        raw_message = {
            "attachments": [],
            "avatar_url": "https://i.groupme.com/1296x972.png.13df1c92895c4aacbf96fd6982a01aa1",
            "created_at": 1507611755,
            "group_id": app.group.group_id,
            "id": "150761175500832461",
            "name": "Foo Bar",
            "sender_id": "abcdef",
            "sender_type": "user",
            "source_guid": "2d01305a-da39-47f6-b293-9b6ef8708c54",
            "system": False,
            "text": "",
            "user_id": "abcdef"
        }

        ret = handlers.mars(Message.from_json(app.gmi, raw_message))

        assert not ret

