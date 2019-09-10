# -*- coding: utf-8 -*-

import logging

from django.http import HttpRequest
from rest_framework.request import Request

from saucerbot.groupme.handlers import registry
from saucerbot.groupme.serializers import BotSerializer

logger = logging.getLogger(__name__)


@registry.handler()
def handler_test1(bot):
    return False


@registry.handler()
def handler_test2(bot):
    return False


@registry.handler()
def handler_test3(bot):
    return False


@registry.handler()
def handler_test4(bot):
    return False


def ensure_post(data, ret):
    def callback(request, context):
        assert request.json() == data

        return ret

    return callback


def test_bot_create_invalid(bot):
    from lowerpines.group import Group

    group = Group(bot.bot.gmi, name='serializer test group')
    group.save()

    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    serializer = BotSerializer(data={}, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'name', 'slug', 'group'}

    serializer = BotSerializer(data={'name': 'test'}, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'slug', 'group'}

    serializer = BotSerializer(data={'slug': 'floop'}, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'name', 'group'}

    serializer = BotSerializer(data={'group': group.group_id}, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'name', 'slug'}

    serializer = BotSerializer(data={'name': 'test', 'slug': 'floop'},
                               context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'group'}

    serializer = BotSerializer(data={'name': 'test', 'group': group.group_id},
                               context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'slug'}

    serializer = BotSerializer(data={'slug': 'floop', 'group': group.group_id},
                               context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'name'}


def test_invalid_group(bot):
    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': '12345',
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'group'}
    assert 'doesn\'t exist' in serializer.errors['group'][0]


def test_bot_create_empty(bot):
    from lowerpines.group import Group

    group = Group(bot.bot.gmi, name='serializer test group')
    group.save()

    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})

    assert serializer.is_valid()

    new_bot = serializer.save(owner=bot.owner)
    gmi_bot = bot.bot.gmi.bots.get(name='test')

    assert new_bot.name == 'test'
    assert new_bot.slug == 'floop'
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 0
    assert gmi_bot.callback_url == 'https://localhost/groupme/api/bots/floop/callback/'
    assert gmi_bot.name == 'test'


def test_bot_create(bot):
    from lowerpines.group import Group

    group = Group(bot.bot.gmi, name='serializer test group')
    group.save()

    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
        'handlers': None
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'handlers'}

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
        'handlers': ['fok']
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'handlers'}

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
        'handlers': ['handler_test1']
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})
    assert serializer.is_valid()

    new_bot = serializer.save(owner=bot.owner)
    gmi_bot = bot.bot.gmi.bots.get(name='test')

    assert new_bot.name == 'test'
    assert new_bot.slug == 'floop'
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 1
    assert gmi_bot.callback_url == 'https://localhost/groupme/api/bots/floop/callback/'
    assert gmi_bot.name == 'test'


def test_bot_update(bot):
    from lowerpines.group import Group

    group = Group(bot.bot.gmi, name='serializer test group')
    group.save()

    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
        'handlers': ['handler_test1', 'handler_test2']
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})
    assert serializer.is_valid()

    new_bot = serializer.save(owner=bot.owner)
    gmi_bot = bot.bot.gmi.bots.get(name='test')

    new_bot_handlers = set(h.handler_name for h in new_bot.handlers.all())

    assert new_bot.name == 'test'
    assert new_bot.slug == 'floop'
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 2
    assert new_bot_handlers == {'handler_test1', 'handler_test2'}
    assert gmi_bot.callback_url == 'https://localhost/groupme/api/bots/floop/callback/'
    assert gmi_bot.name == 'test'

    data = {
        'name': 'new_test',
        'slug': 'new_floop',
        'group': group.group_id,
        'handlers': ['handler_test1', 'handler_test3', 'handler_test4']
    }

    serializer = BotSerializer(new_bot, data=data, partial=False, context={'request': fake_request})
    assert serializer.is_valid()

    updated_bot = serializer.save()

    updated_bot_handlers = set(h.handler_name for h in updated_bot.handlers.all())

    assert updated_bot.name == 'new_test'
    assert updated_bot.slug == 'new_floop'
    assert updated_bot.bot_id == gmi_bot.bot_id
    assert updated_bot.group_id == group.group_id
    assert updated_bot.handlers.count() == 3
    assert updated_bot_handlers == {'handler_test1', 'handler_test3', 'handler_test4'}

    # uncomment when we fix this
    # assert gmi_bot.callback_url == 'https://localhost/groupme/api/bots/new_floop/callback/'
    # assert gmi_bot.name == 'new_test'


def test_bot_failed_update(bot):
    from lowerpines.group import Group

    group = Group(bot.bot.gmi, name='serializer test group')
    group.save()

    group2 = Group(bot.bot.gmi, name='serializer test group2')
    group2.save()

    fake_request = Request(HttpRequest())
    fake_request.user = bot.owner

    data = {
        'name': 'test',
        'slug': 'floop',
        'group': group.group_id,
        'handlers': ['handler_test1', 'handler_test2']
    }

    serializer = BotSerializer(data=data, context={'request': fake_request})
    assert serializer.is_valid()

    new_bot = serializer.save(owner=bot.owner)
    gmi_bot = bot.bot.gmi.bots.get(name='test')

    new_bot_handlers = set(h.handler_name for h in new_bot.handlers.all())

    assert new_bot.name == 'test'
    assert new_bot.slug == 'floop'
    assert new_bot.bot_id == gmi_bot.bot_id
    assert new_bot.group_id == group.group_id
    assert new_bot.handlers.count() == 2
    assert new_bot_handlers == {'handler_test1', 'handler_test2'}
    assert gmi_bot.callback_url == 'https://localhost/groupme/api/bots/floop/callback/'
    assert gmi_bot.name == 'test'

    data = {
        'name': 'new_test',
        'slug': 'new_floop',
        'group': group2.group_id,
        'handlers': ['handler_test1', 'handler_test3', 'handler_test4']
    }

    serializer = BotSerializer(new_bot, data=data, partial=False, context={'request': fake_request})

    assert not serializer.is_valid()
    assert set(serializer.errors.keys()) == {'group'}
    assert 'may not be changed' in serializer.errors['group'][0]
