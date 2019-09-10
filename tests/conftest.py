# -*- coding: utf-8 -*-

import uuid
from collections import defaultdict

import pytest

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
        },
        {
            "id": "1234567",
            "group_id": "1234567",
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
            "members": [],
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


@pytest.fixture()
def lowerpines_mock(monkeypatch):
    from lowerpines.bot import Bot
    from lowerpines.group import Group
    from lowerpines.message import Message
    from lowerpines.endpoints.group import GroupMessagesManager
    from lowerpines.user import User
    from lowerpines.exceptions import InvalidOperationException
    from lowerpines.message import smart_split_complex_message

    global_users = {}
    global_bots = {}
    global_groups = {}
    global_messages = defaultdict(list)

    class TestUser(User):

        def save(self):
            global_users[self.gmi.access_token] = self

        def refresh(self):
            if self.gmi.access_token in global_users:
                self._refresh_from_other(global_users[self.gmi.access_token])

    class TestGroup(Group):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.messages = TestGroupMessageManager(self)

        def save(self):
            if not self.group_id:
                self.group_id = str(uuid.uuid4()).replace('-', '')
            global_groups[self.group_id] = self

        def delete(self):
            if self.group_id in global_groups:
                del global_groups[self.group_id]

        def refresh(self):
            pass

        @staticmethod
        def get_all(gmi):
            return global_groups.values()

        @staticmethod
        def get(gmi, group_id):
            return global_groups.get(group_id)

    class TestGroupMessageManager(GroupMessagesManager):

        @property
        def count(self):
            return len(global_messages[self.group.group_id])

        def all(self):
            return global_messages[self.group.group_id]

        def recent(self, count=100):
            return global_messages[self.group.group_id][-count:]

        def before(self, message, count=100):
            group_messages = global_messages[self.group.group_id]
            idx = group_messages.index(message)
            return group_messages[max(idx - count, 0):idx]

        def since(self, message, count=100):
            group_messages = global_messages[self.group.group_id]
            idx = group_messages.index(message)
            return group_messages[idx:min(idx + count, len(group_messages))]

    class TestMessage(Message):

        def save(self):
            if self.message_id:
                raise InvalidOperationException(
                    "You cannot change a message that has already been sent")
            else:
                self.message_id = str(uuid.uuid4()).replace('-', '')
                global_messages[self.group_id].append(self)

        def refresh(self):
            pass

        def like(self):
            if self.favorited_by is None:
                self.favorited_by = set()
            self.favorited_by.add(self.gmi.user.get().user_id)

        def like_as(self, user_id):
            if self.favorited_by is None:
                self.favorited_by = set()
            self.favorited_by.add(user_id)

        @classmethod
        def from_json(cls, gmi, json_dict, *args):
            return Message.from_json(gmi, json_dict, *args)

    class TestBot(Bot):

        def save(self):
            if self.bot_id is None:
                self.bot_id = str(uuid.uuid4()).replace('-', '')

            global_bots[self.bot_id] = self

        def delete(self):
            if self.bot_id in global_bots:
                del global_bots[self.bot_id]

        def post(self, text):
            text, attachments = smart_split_complex_message(text)
            message = TestMessage(self.gmi, group_id=self.group_id, text=text,
                                  attachments=attachments)
            message.name = self.name
            message.save()

        @staticmethod
        def get_all(gmi):
            return global_bots.values()

    monkeypatch.setattr('lowerpines.user.User', TestUser)
    monkeypatch.setattr('lowerpines.endpoints.user.User', TestUser)
    monkeypatch.setattr('lowerpines.group.Group', TestGroup)
    monkeypatch.setattr('lowerpines.endpoints.group.Group', TestGroup)
    monkeypatch.setattr('lowerpines.message.Message', TestMessage)
    monkeypatch.setattr('lowerpines.endpoints.message.Message', TestMessage)
    monkeypatch.setattr('lowerpines.bot.Bot', TestBot)
    monkeypatch.setattr('lowerpines.endpoints.bot.Bot', TestBot)


@pytest.fixture(name='bot')
def setup_bot(db, lowerpines_mock):
    """
    Create a bot for saucerbot tests
    """
    from lowerpines.group import Group
    from saucerbot.groupme.models import User, Bot

    user = User.objects.create(access_token='123456', user_id='123456')

    group = Group(user.gmi, name='test group')
    group.save()

    bot = Bot.objects.create(owner=user, group=group,
                             name='saucerbot', slug='saucerbot')

    # Cache these
    bot.bot
    bot.bot.group

    # Then return the bot
    yield bot

    # Clear the GMI cache when we're done
    from saucerbot.groupme.models import get_gmi
    get_gmi.cache_clear()
