# -*- coding: utf-8 -*-

import json
import logging
import uuid

logger = logging.getLogger(__name__)


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
        'source_guid': str(uuid.uuid4()),
        'system': False,
        'text': text,
        'user_id': "abcdef"
    }


def test_mars(bot):
    from lowerpines.message import Message
    from saucerbot.groupme.handlers import general

    raw_message = get_sample_message(bot.bot, "", [{'type': "image"}])

    ret = general.mars(bot.bot, Message.from_json(bot.bot.gmi, raw_message), 1)

    assert ret
    assert bot.group.messages.count == 1

    posted = bot.group.messages.all()[0]

    assert posted.text is not None
    assert len(posted.text) > 0
    assert len(posted.attachments) == 1
    assert posted.attachments[0]['type'] == 'mentions'
    assert posted.attachments[0]['user_ids'] == ['abcdef']


def test_mars_no_message(bot):
    from lowerpines.message import Message
    from saucerbot.groupme.handlers import general

    raw_message = get_sample_message(bot.bot, "", [])

    ret = general.mars(bot.bot, Message.from_json(bot.bot.gmi, raw_message), 1)

    assert not ret
    assert bot.group.messages.count == 0


def test_zo(bot, client):
    expected_post = "Zo is dead.  Long live saucerbot."

    # Try once before the handler is registered
    sample_message = get_sample_message(bot.bot, 'zo')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}

    # Then register & continue
    bot.handlers.create(handler_name='zo_is_dead')

    sample_message = get_sample_message(bot.bot, 'zo')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert bot.group.messages.all()[0].text == expected_post

    sample_message = get_sample_message(bot.bot, 'hey there bot hey')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 2
    assert bot.group.messages.all()[0].text == expected_post
    assert bot.group.messages.all()[1].text == expected_post

    sample_message = get_sample_message(bot.bot, 'bot')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 2
    assert bot.group.messages.all()[0].text == expected_post
    assert bot.group.messages.all()[1].text == expected_post
