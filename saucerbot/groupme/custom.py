# -*- coding: utf-8 -*-

"""
Module to replace the root groupy package that requires the API key to be in a file
"""

from typing import Any, Dict, List, Optional

from groupy import config
from groupy.api import endpoint
from groupy.object.attachments import Attachment
from groupy.object.responses import (
    Bot as GroupyBot,
    Group as GroupyGroup,
    Message as GroupyMessage,
    Recipient,
)


class Bot(GroupyBot):

    def __init__(self, **kwargs) -> None:
        super(Bot, self).__init__(**kwargs)

    @classmethod
    def get(cls, bot_id: str) -> Optional['Bot']:
        if not bot_id:
            return None

        for bot in endpoint.Bots.index():
            if bot['bot_id'] == bot_id:
                return cls(**bot)
        return None

    def post(self, text: str, *attachments: Attachment, picture_url: str = None) -> bool:
        text = text.format(emoji=config.EMOJI_PLACEHOLDER)
        raw_attachments: List[Dict] = [a.as_dict() for a in attachments]
        return super(Bot, self).post(text, *raw_attachments, picture_url=picture_url)


class Message(GroupyMessage):

    def __init__(self, recipient: Recipient, **kwargs) -> None:
        super(Message, self).__init__(recipient, **kwargs)

        # Save a couple extra properties
        self.sender_id: str = kwargs.get('sender_id')
        self.sender_type: str = kwargs.get('sender_type')


class Group(GroupyGroup):

    def __init__(self, **kwargs) -> None:
        super(Group, self).__init__(**kwargs)

    @classmethod
    def get(cls, group_id: str) -> 'Group':
        """
        Refresh the group information from the API.
        """
        return cls(**endpoint.Groups.show(group_id))

    def bot_message(self, message: Dict[str, Any]) -> Message:
        return Message(self, **message)
