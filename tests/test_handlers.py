# -*- coding: utf-8 -*-

import json
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_sample_message(bot, text, attachments=None, system=False, name='Foo Bar'):
    return {
        'attachments': attachments or [],
        'avatar_url': "https://example.com/avatar.jpeg",
        'created_at': int(datetime.now().timestamp()),
        'group_id': bot.group.group_id,
        'id': "1234567890",
        'name': name,
        'sender_id': "abcdef",
        'sender_type': "user",
        'source_guid': str(uuid.uuid4()),
        'system': system,
        'text': text,
        'user_id': "abcdef"
    }


def test_mars(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import general

    raw_message = get_sample_message(bot.bot, "", [{'type': "image"}])

    ret = general.mars(bot.bot, Message.from_json(gmi, raw_message), 1)

    assert ret
    assert bot.group.messages.count == 1

    posted = bot.group.messages.all()[0]

    assert posted.text is not None
    assert len(posted.text) > 0
    assert len(posted.attachments) == 1
    assert posted.attachments[0]['type'] == 'mentions'
    assert posted.attachments[0]['user_ids'] == ['abcdef']


def test_mars_no_message(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import general

    raw_message = get_sample_message(bot.bot, "", [])

    ret = general.mars(bot.bot, Message.from_json(gmi, raw_message), 1)

    assert not ret
    assert bot.group.messages.count == 0


ZO_EXPECTED_POST = "Zo is dead.  Long live saucerbot."


def test_zo_unregistered(bot, client):
    # Try once before the handler is registered
    sample_message = get_sample_message(bot.bot, 'zo')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_zo_zo(bot, client):
    bot.handlers.create(handler_name='zo_is_dead')

    sample_message = get_sample_message(bot.bot, 'zo')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert bot.group.messages.all()[0].text == ZO_EXPECTED_POST


def test_zo_bot(bot, client):
    bot.handlers.create(handler_name='zo_is_dead')

    sample_message = get_sample_message(bot.bot, 'hey there bot hey')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert bot.group.messages.all()[0].text == ZO_EXPECTED_POST


def test_zo_bot_bad(bot, client):
    bot.handlers.create(handler_name='zo_is_dead')

    sample_message = get_sample_message(bot.bot, 'bot')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_system_messages_unregistered(bot, client):
    # Try once before the handler is registered
    sample_message = get_sample_message(bot.bot, 'foo changed name to bar', system=True)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_name_change(bot, client):
    bot.handlers.create(handler_name='system_messages')

    sample_message = get_sample_message(bot.bot, 'foo changed name to bar', system=True)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert len(bot.group.messages.recent(1)[0].attachments) == 1


def test_user_add(bot, client):
    bot.handlers.create(handler_name='system_messages')

    sample_message = get_sample_message(bot.bot, 'foo added baz to the group.', system=True)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert len(bot.group.messages.recent(1)[0].attachments) == 1


def test_user_remove(bot, client):
    bot.handlers.create(handler_name='system_messages')

    sample_message = get_sample_message(bot.bot, 'foo removed baz from the group.', system=True)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert len(bot.group.messages.recent(1)[0].attachments) == 1


def test_bogus_system(bot, client):
    bot.handlers.create(handler_name='system_messages')

    sample_message = get_sample_message(bot.bot, 'bogus message', system=True)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_non_system(bot, client):
    bot.handlers.create(handler_name='system_messages')

    sample_message = get_sample_message(bot.bot, 'foo removed baz from the group.', system=False)

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_saucerbot_user_not(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import saucer

    raw_message = get_sample_message(bot.bot, "")

    ret = saucer.user_named_saucerbot(bot.bot, Message.from_json(gmi, raw_message))

    assert not ret
    assert bot.group.messages.count == 0


def test_saucerbot_user(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import saucer

    raw_message = get_sample_message(bot.bot, "", name='saucerbot')

    ret = saucer.user_named_saucerbot(bot.bot, Message.from_json(gmi, raw_message))

    assert ret
    assert bot.group.messages.count == 1


def test_saucerbot_user_random(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import saucer

    raw_message = get_sample_message(bot.bot, "", name='saucerbot')

    ret = saucer.user_named_saucerbot(bot.bot, Message.from_json(gmi, raw_message), True)

    assert ret
    assert bot.group.messages.count == 1


def test_save_id_unregistered(bot, client, monkeypatch):
    monkeypatch.setattr('saucerbot.utils.base.get_tasted_brews', lambda x: [{'name': 'beer'}])

    # Try once before the handler is registered
    sample_message = get_sample_message(bot.bot, 'my saucer id is 123456')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': False}
    assert bot.group.messages.count == 0


def test_save_id_invalid(bot, client, monkeypatch):
    def get_tasted_brews(x):
        return []

    monkeypatch.setattr('saucerbot.utils.get_tasted_brews', get_tasted_brews)
    monkeypatch.setattr('saucerbot.groupme.models.get_tasted_brews', get_tasted_brews)
    monkeypatch.setattr('saucerbot.groupme.handlers.saucer.get_tasted_brews', get_tasted_brews)

    bot.handlers.create(handler_name='save_saucer_id')

    sample_message = get_sample_message(bot.bot, 'my saucer id is 123456')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert "isn't a valid Saucer ID" in bot.group.messages.all()[0].text


def test_save_id_valid(bot, client, monkeypatch):
    def get_tasted_brews(x):
        return [{'name': 'beer'}]

    monkeypatch.setattr('saucerbot.utils.get_tasted_brews', get_tasted_brews)
    monkeypatch.setattr('saucerbot.groupme.models.get_tasted_brews', get_tasted_brews)
    monkeypatch.setattr('saucerbot.groupme.handlers.saucer.get_tasted_brews', get_tasted_brews)

    bot.handlers.create(handler_name='save_saucer_id')

    sample_message = get_sample_message(bot.bot, 'my saucer id is 123456')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1
    assert "isn't a valid Saucer ID" not in bot.group.messages.all()[0].text


def test_troll_missing(bot, client):
    bot.handlers.create(handler_name='troll')

    sample_message = get_sample_message(bot.bot, 'we play pong')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1

    posted_message = bot.group.messages.all()[0]

    assert posted_message.text == "Shaina is the troll"
    assert len(posted_message.attachments) == 0


def test_troll_present(bot, gmi, client):
    bot.handlers.create(handler_name='troll')

    from lowerpines.endpoints.member import Member
    from saucerbot.groupme.handlers.saucer import SHAINA_USER_ID

    random = Member(gmi, bot.group.group_id, 'Random', '123456')
    bot.group.add_member(random)

    shaina = Member(gmi, bot.group.group_id, 'Shaina', SHAINA_USER_ID)
    bot.group.add_member(shaina)

    sample_message = get_sample_message(bot.bot, 'beer pong')

    ret = client.post('/groupme/api/bots/saucerbot/callback/', content_type='application/json',
                      data=json.dumps(sample_message))

    assert ret.status_code == 200
    assert ret.json() == {'message_sent': True}
    assert bot.group.messages.count == 1

    posted_message = bot.group.messages.all()[0]

    assert posted_message.text == "@Shaina is the troll"
    assert len(posted_message.attachments) == 1


def test_whoami(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import general
    from saucerbot.groupme.models import HistoricalNickname

    fake_user_id = '123456'

    HistoricalNickname.objects.create(group_id=bot.group_id, groupme_id=fake_user_id,
                                      nickname='abc123', timestamp=datetime.now() - timedelta(1))
    HistoricalNickname.objects.create(group_id=bot.group_id, groupme_id=fake_user_id,
                                      nickname='def456', timestamp=datetime.now() - timedelta(2))

    message = Message(gmi)
    message.user_id = fake_user_id

    general.whoami(bot.bot, message)

    assert bot.group.messages.count == 1
    assert bot.group.messages.all()[0].text == 'abc123 a day ago\ndef456 2 days ago\n'


def test_whoami_long(bot, gmi):
    from lowerpines.endpoints.message import Message
    from saucerbot.groupme.handlers import general
    from saucerbot.groupme.models import HistoricalNickname

    long_nickname = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    fake_user_id = '123456'

    for i in range(1, 21):
        HistoricalNickname.objects.create(group_id=bot.group_id, groupme_id=fake_user_id,
                                          nickname=f'{long_nickname} {i}',
                                          timestamp=datetime.now() - timedelta(i))

    message = Message(gmi)
    message.user_id = fake_user_id

    general.whoami(bot.bot, message)

    assert bot.group.messages.count == 2

    first_message = bot.group.messages.all()[0]

    assert len(first_message.text) <= 1000

    first_expected_start = f'{long_nickname} 1 a day ago\n' \
                           f'{long_nickname} 2 2 days ago\n'

    first_expected_end = f'{long_nickname} 14 2 weeks ago\n' \
                         f'{long_nickname} 15 2 weeks ago\n'

    assert first_message.text.startswith(first_expected_start)
    assert first_message.text.endswith(first_expected_end)

    second_message = bot.group.messages.all()[1]

    assert len(second_message.text) <= 1000

    second_expected_start = f'{long_nickname} 16 2 weeks ago\n' \
                            f'{long_nickname} 17 2 weeks ago\n'

    second_expected_end = f'{long_nickname} 19 2 weeks ago\n' \
                          f'{long_nickname} 20 2 weeks ago\n'

    assert second_message.text.startswith(second_expected_start)
    assert second_message.text.endswith(second_expected_end)
