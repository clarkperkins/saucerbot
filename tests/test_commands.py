# -*- coding: utf-8 -*-

import logging

from django.core.management import execute_from_command_line

from saucerbot.groupme.management.commands.remind import LIKE_IF_POST

logger = logging.getLogger(__name__)


def test_like_if(bot):
    execute_from_command_line(['manage.py', 'remind', 'saucerbot', '--force', 'like-if'])

    assert bot.group.messages.count == 1
    assert bot.group.messages.all()[0].text == LIKE_IF_POST


def test_whos_coming(bot, gmi):
    from lowerpines.endpoints.member import Member

    test_user1 = Member(gmi, bot.group.group_id, 'Test 1', '1')
    test_user2 = Member(gmi, bot.group.group_id, 'Test 2', '2')
    test_user3 = Member(gmi, bot.group.group_id, 'Test 3', '3')

    bot.group.add_member(test_user1)
    bot.group.add_member(test_user2)
    bot.group.add_member(test_user3)

    # Add the like if post first
    bot.post_message(LIKE_IF_POST)
    bot.group.messages.all()[0].like_as('1')
    bot.group.messages.all()[0].like_as('2')
    bot.group.messages.all()[0].like_as('3')

    execute_from_command_line(['manage.py', 'remind', 'saucerbot', '--force', 'whos-coming'])

    assert bot.group.messages.count == 3
    assert bot.group.messages.all()[0].text == LIKE_IF_POST
    assert bot.group.messages.all()[1].text == "Looks like 3 people are coming tonight."
    assert bot.group.messages.all()[2].text == "Save seats for:\n  @Test 1\n  @Test 2\n  @Test 3"


def test_whos_coming_missing_users(bot):
    # Add the like if post first
    bot.post_message(LIKE_IF_POST)
    bot.group.messages.all()[0].like_as('1')
    bot.group.messages.all()[0].like_as('2')
    bot.group.messages.all()[0].like_as('3')

    execute_from_command_line(['manage.py', 'remind', 'saucerbot', '--force', 'whos-coming'])

    assert bot.group.messages.count == 2
    assert bot.group.messages.all()[0].text == LIKE_IF_POST
    assert bot.group.messages.all()[1].text == "Looks like 3 people are coming tonight."
