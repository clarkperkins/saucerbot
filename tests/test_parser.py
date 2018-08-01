# -*- coding: utf-8 -*-

import io
import json
import logging
from typing import BinaryIO

from rest_framework.exceptions import ParseError

from saucerbot.groupme.parsers import GroupMeMessageParser

logger = logging.getLogger(__name__)

SAMPLE_MESSAGE = {
    'attachments': [],
    'avatar_url': "https://example.com/avatar.jpeg",
    'created_at': 1507611755,
    'group_id': "1234567890",
    'id': "1234567890",
    'name': "Foo Bar",
    'sender_id': "abcdef",
    'sender_type': "user",
    'source_guid': "2d01305a-da39-47f6-b293-9b6ef8708c54",
    'system': False,
    'text': "I sent a message",
    'user_id': "abcdef"
}


class IOHelper(io.BytesIO):

    def __init__(self, initial_bytes=None):
        super().__init__(initial_bytes)
        self.wrapper = io.TextIOWrapper(self)


def get_stream(data: dict) -> BinaryIO:
    """
    Build a raw stream containing the serialized json provided from data.
    The caller is responsible for closing the returned stream.
    :param data: dict to serialize
    :return:
    """
    stream = IOHelper()

    # use the underlying wrapper
    json.dump(data, stream.wrapper, ensure_ascii=False)
    stream.wrapper.seek(0)

    return stream


def test_groupme_parser():
    parser = GroupMeMessageParser()

    with get_stream(SAMPLE_MESSAGE) as stream:
        message = parser.parse(stream)

    assert message.name == "Foo Bar"
    assert message.attachments == []
    assert message.user_id == "abcdef"

    with get_stream({}) as stream:
        try:
            parser.parse(stream)
            raise AssertionError('Expected a parse error')
        except ParseError:
            pass
