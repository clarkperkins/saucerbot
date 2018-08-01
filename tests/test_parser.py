# -*- coding: utf-8 -*-

import io
import json
import logging

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


def test_groupme_parser():
    parser = GroupMeMessageParser()

    # Build the stream as expected by the parser
    with io.BytesIO() as stream, io.TextIOWrapper(stream) as wrapper:
        json.dump(SAMPLE_MESSAGE, wrapper)
        wrapper.seek(0)

        message = parser.parse(stream)

    assert message.name == "Foo Bar"
    assert message.attachments == []
    assert message.user_id == "abcdef"

    with io.BytesIO() as stream, io.TextIOWrapper(stream) as wrapper:
        wrapper.write("{}")
        wrapper.seek(0)

        try:
            parser.parse(stream)
            raise AssertionError('Expected a parse error')
        except ParseError:
            pass
