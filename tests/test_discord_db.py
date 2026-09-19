# -*- coding: utf-8 -*-

import threading

import pytest
from asgiref.sync import sync_to_async

from saucerbot.discord.db import close_stale_connections, with_db_lifecycle


@pytest.mark.asyncio
async def test_closes_connections_on_the_orm_thread(monkeypatch):
    """
    django's connection storage is thread local and the async ORM runs its
    queries on asgiref's thread sensitive executor.  If we closed connections
    from the event loop thread instead we would be looking at a different (and
    empty) set of connections, so the stale one would survive and every query
    would keep failing.
    """
    closed_on: list[int] = []

    monkeypatch.setattr(
        "saucerbot.discord.db.close_old_connections",
        lambda: closed_on.append(threading.get_ident()),
    )

    orm_thread = await sync_to_async(threading.get_ident)()

    await close_stale_connections()

    assert closed_on == [orm_thread]
    assert orm_thread != threading.get_ident()


@pytest.mark.asyncio
async def test_lifecycle_closes_around_the_event(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        "saucerbot.discord.db.close_old_connections", lambda: calls.append("close")
    )

    @with_db_lifecycle
    async def handler():
        calls.append("handler")
        return "done"

    assert await handler() == "done"
    assert calls == ["close", "handler", "close"]


@pytest.mark.asyncio
async def test_lifecycle_closes_after_a_failing_event(monkeypatch):
    """
    A handler blowing up is exactly when a connection is most likely to be in a
    bad state, so the trailing close has to happen even on the error path.
    """
    calls: list[str] = []

    monkeypatch.setattr(
        "saucerbot.discord.db.close_old_connections", lambda: calls.append("close")
    )

    @with_db_lifecycle
    async def handler():
        calls.append("handler")
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await handler()

    assert calls == ["close", "handler", "close"]


def test_lifecycle_preserves_metadata():
    @with_db_lifecycle
    async def on_something(arg):
        """docstring"""
        return arg

    assert on_something.__name__ == "on_something"
    assert on_something.__doc__ == "docstring"


@pytest.mark.parametrize(
    "event_name",
    ["on_message", "on_reaction_add", "on_member_join", "on_member_update"],
)
def test_db_touching_events_are_wrapped(event_name):
    """
    Every discord event is its own "request" boundary, so a new one that reaches
    the database needs the decorator too.  This is the easy thing to forget.
    """
    from saucerbot.discord.client import SaucerbotClient

    event = getattr(SaucerbotClient, event_name)
    assert (
        getattr(event, "__wrapped__", None) is not None
    ), f"{event_name} is not wrapped with @with_db_lifecycle"
