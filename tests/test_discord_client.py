# -*- coding: utf-8 -*-

from datetime import timedelta

import arrow
import discord.ext.test as dpytest
import pytest


@pytest.fixture(name="client")
def setup_client(db, event_loop):
    from saucerbot.discord.client import SaucerbotClient

    client = SaucerbotClient(loop=event_loop)
    dpytest.configure(client)
    return client


@pytest.mark.asyncio
async def test_ready(client):
    await client.on_ready()


@pytest.mark.asyncio
async def test_basic_message(client):
    await dpytest.message("test")
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_whoami(client, event_loop):
    from saucerbot.discord.models import HistoricalDisplayName

    fake_guild_id = "abcdef"
    fake_user_id = "123456"

    def create_data():
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

    await event_loop.run_in_executor(None, create_data)

    response = await client.get_whoami_response(fake_guild_id, fake_user_id)

    assert response == "abc123 a day ago\ndef456 2 days ago\n"
