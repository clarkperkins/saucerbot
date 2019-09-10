# -*- coding: utf-8 -*-

import uuid
from collections import defaultdict

import pytest


@pytest.fixture(name='gmi')
def gmi(monkeypatch):
    from lowerpines.bot import Bot
    from lowerpines.endpoints.group import GroupMessagesManager
    from lowerpines.exceptions import InvalidOperationException
    from lowerpines.group import Group
    from lowerpines.message import Message, smart_split_complex_message
    from lowerpines.user import User

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

    class TestGMI:
        def __init__(self):
            self.groups = None
            self.bots = None
            self.chats = None
            self.user = None

            self.refresh()

        def refresh(self):
            from lowerpines.group import GroupManager
            from lowerpines.bot import BotManager
            from lowerpines.chat import ChatManager
            from lowerpines.user import UserManager

            self.groups = GroupManager(self)
            self.bots = BotManager(self)
            self.chats = ChatManager(self)
            self.user = UserManager(self)

        def convert_image_url(self, url):
            return url

    return TestGMI()


@pytest.fixture(name='bot')
def setup_bot(db, gmi, monkeypatch):
    """
    Create a bot for saucerbot tests
    """
    monkeypatch.setattr('saucerbot.groupme.models.get_gmi', lambda a: gmi)

    from lowerpines.group import Group
    from saucerbot.groupme.models import User, Bot

    user = User.objects.create(access_token='123456', user_id='123456')

    group = Group(user.gmi, name='test group')
    group.save()

    bot = Bot.objects.create(owner=user, group=group,
                             name='saucerbot', slug='saucerbot')

    return bot
