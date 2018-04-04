# -*- coding: utf-8 -*-

import pytest
import requests_mock


GROUPME_API_URL = 'https://api.groupme.com/v3'


BOTS = {
    "meta": {
        "code": 200
    },
    "response": [
        {
            "name": "saucerbot",
            "bot_id": "123456",
            "group_id": "123456",
            "group_name": "SaucerBot Beta",
            "avatar_url": "https://i.groupme.com/2008x2008.jpeg.94ee8b6877ae47a1aaef95f4e0f54e72",
            "callback_url": "https://saucerbot-staging.herokuapp.com/hooks/groupme/",
            "dm_notification": False
        }
    ]
}

GROUP = {
    "response": [
        {
            "id": "123456",
            "group_id": "123456",
            "name": "SaucerBot Beta",
            "phone_number": "+1 6316259288",
            "type": "private",
            "description": "Place to test out new saucerbot functionality without annoying the whole group",
            "image_url": None,
            "creator_user_id": "6499167",
            "created_at": 1504139876,
            "updated_at": 1507593705,
            "office_mode": False,
            "share_url": None,
            "share_qr_code_url": None,
            "members": [
                {
                    "user_id": "6499167",
                    "nickname": "Clark Perkins",
                    "image_url": "https://i.groupme.com/750x750.jpeg.15c839da4df14886b7ad4b4fbf8ec9c9",
                    "id": "268021690",
                    "muted": False,
                    "autokicked": False,
                    "roles": [
                        "admin",
                        "owner"
                    ]
                },
                {
                    "user_id": "13032590",
                    "nickname": "Emma Jackson",
                    "image_url": "https://i.groupme.com/1944x1944.jpeg.ef937b6165dd4e9680b0b6a5d7eb6339",
                    "id": "268024549",
                    "muted": False,
                    "autokicked": False,
                    "roles": [
                        "user"
                    ]
                },
                {
                    "user_id": "8813987",
                    "nickname": "Christian Reynolds",
                    "image_url": "http://i.groupme.com/b74caa706e790130ead122000a1d94cf",
                    "id": "269394452",
                    "muted": True,
                    "autokicked": False,
                    "roles": [
                        "user"
                    ]
                }
            ],
            "messages": {
                "count": 450,
                "last_message_id": "150759370544643171",
                "last_message_created_at": 1507593705,
                "preview": {
                    "nickname": "saucerbot",
                    "text": "Looks like nobody is coming tonight.",
                    "image_url": "https://i.groupme.com/2008x2008.jpeg.94ee8b6877ae47a1aaef95f4e0f54e72",
                    "attachments": []
                }
            },
            "max_members": 200
        }
    ],
    "meta": {
        "code": 200
    }
}


@pytest.fixture(name='bot')
def setup_bot(monkeypatch, tmpdir):
    """
    Create a bot for saucerbot tests
    """
    monkeypatch.setenv('GROUPME_API_KEY', '123456')
    monkeypatch.setenv('GROUPME_BOT_ID', '123456')
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmpdir}/test.db')

    with requests_mock.Mocker() as m:
        m.get(GROUPME_API_URL + '/bots', json=BOTS)
        m.get(GROUPME_API_URL + '/groups?page=1&per_page=100', json=GROUP)

        # Just import the app and return it
        from saucerbot.groupme.utils import get_bot, get_group

        # Cache the group first
        get_group()

        # Then return the bot
        return get_bot()
