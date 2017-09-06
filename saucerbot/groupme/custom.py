# -*- coding: utf-8 -*-

"""
Module to replace the root groupy package that requires the API key to be in a file
"""

from groupy import config

from groupy.api import endpoint
from groupy.api.errors import GroupMeError
from groupy.object.responses import (
    Bot as GroupyBot,
    Group as GroupyGroup,
    Message as GroupyMessage,
)


class Bot(GroupyBot):

    def __init__(self, **kwargs):
        super(Bot, self).__init__(**kwargs)

    @classmethod
    def get(cls, bot_id):
        for bot in endpoint.Bots.index():
            if bot['bot_id'] == bot_id:
                return Bot(**bot)
        return None

    def post(self, text, *attachments, picture_url=None):
        text = text.format(emoji=config.EMOJI_PLACEHOLDER)
        attachments = [a.as_dict() for a in attachments]
        return super(Bot, self).post(text, *attachments, picture_url=picture_url)


class Message(GroupyMessage):

    def __init__(self, recipient, **kwargs):
        super(Message, self).__init__(recipient, **kwargs)

        # Save a couple extra properties
        self.sender_id = kwargs.get('sender_id')
        self.sender_type = kwargs.get('sender_type')


class Group(GroupyGroup):

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)

    @classmethod
    def get(cls, group_id):
        """Refresh the group information from the API.
        """
        return Group(**endpoint.Groups.show(group_id))

    def bot_message(self, message):
        return Message(self, **message)
