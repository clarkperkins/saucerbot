# -*- coding: utf-8 -*-

from datetime import timedelta

import arrow
import discord.ext.test as dpytest
import pytest


@pytest.mark.asyncio
async def test_ready(discord_client):
    await discord_client.on_ready()


@pytest.mark.asyncio
async def test_basic_message(discord_client):
    await dpytest.message("test")
    assert dpytest.verify().message().nothing()


def test_whoami(db):
    from saucerbot.discord.client import get_whoami_responses
    from saucerbot.discord.models import HistoricalDisplayName

    fake_guild_id = "abcdef"
    fake_user_id = "123456"

    HistoricalDisplayName.objects.create(
        guild_id=fake_guild_id,
        user_id=fake_user_id,
        display_name="abc123",
        timestamp=arrow.utcnow().datetime - timedelta(1),
    )
    HistoricalDisplayName.objects.create(
        guild_id=fake_guild_id,
        user_id=fake_user_id,
        display_name="def456",
        timestamp=arrow.utcnow().datetime - timedelta(2),
    )

    responses = get_whoami_responses(fake_guild_id, fake_user_id)

    assert len(responses) == 1
    assert responses[0] == "abc123 a day ago\ndef456 2 days ago\n"

    for d in HistoricalDisplayName.objects.all():
        d.delete()


def test_whoami_long(db):
    from saucerbot.discord.client import get_whoami_responses
    from saucerbot.discord.models import HistoricalDisplayName

    long_display_name = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    fake_guild_id = "abcdef"
    fake_user_id = "123456"

    for i in range(1, 41):
        HistoricalDisplayName.objects.create(
            guild_id=fake_guild_id,
            user_id=fake_user_id,
            display_name=f"{long_display_name} {i}",
            timestamp=arrow.utcnow().datetime - timedelta(i),
        )

    responses = get_whoami_responses(fake_guild_id, fake_user_id)

    assert len(responses) == 2

    first_message = responses[0]

    assert len(first_message) <= 2000

    first_expected_start = (
        f"{long_display_name} 1 a day ago\n" f"{long_display_name} 2 2 days ago\n"
    )

    first_expected_end = (
        f"{long_display_name} 29 4 weeks ago\n" f"{long_display_name} 30 4 weeks ago\n"
    )

    assert first_message.startswith(first_expected_start)
    assert first_message.endswith(first_expected_end)

    second_message = responses[1]

    assert len(second_message) <= 2000

    second_expected_start = (
        f"{long_display_name} 31 a month ago\n" f"{long_display_name} 32 a month ago\n"
    )

    second_expected_end = (
        f"{long_display_name} 39 a month ago\n" f"{long_display_name} 40 a month ago\n"
    )

    assert second_message.startswith(second_expected_start)
    assert second_message.endswith(second_expected_end)

    for d in HistoricalDisplayName.objects.all():
        d.delete()
