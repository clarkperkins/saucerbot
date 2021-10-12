# -*- coding: utf-8 -*-

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
