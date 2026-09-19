# -*- coding: utf-8 -*-
"""
Database connection lifecycle management for the discord worker.

Django recycles stale/obsolete database connections in ``close_old_connections``,
which it wires up to the ``request_started`` / ``request_finished`` signals.  The
discord worker is a long lived event loop rather than a request/response cycle,
so those signals never fire and a connection is opened once and then reused
forever.  When the server (or a pooler, or a firewall) eventually drops that
connection, every subsequent query fails with ``OperationalError: the connection
is closed`` and the worker stays broken until the process is restarted.

``close_stale_connections`` gives us the request boundary Django is missing by
treating each discord event as the start of a new "request".

Note that ``django.db.connections`` is *thread critical* local state, and the
async ORM runs its queries in asgiref's thread sensitive executor rather than on
the event loop.  Closing connections therefore has to happen on that same
executor thread, otherwise we would be inspecting the event loop thread's
(empty) connection storage and the stale connection would never be reaped.  This
mirrors how django's own ASGI handler dispatches the ``request_started`` signal.
"""

import functools
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from asgiref.sync import sync_to_async
from django.db import close_old_connections

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


async def close_stale_connections() -> None:
    """
    Close any database connections that are unusable or past their max age.

    Runs on asgiref's thread sensitive executor so that it operates on the same
    connections the async ORM actually uses.
    """
    await sync_to_async(close_old_connections, thread_sensitive=True)()


def with_db_lifecycle(
    func: Callable[P, Awaitable[T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Reap stale database connections before and after a discord event handler.

    Closing beforehand means a connection dropped while the worker was idle is
    replaced rather than raising, and closing afterwards keeps us from holding an
    idle connection open between events.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        await close_stale_connections()
        try:
            return await func(*args, **kwargs)
        finally:
            await close_stale_connections()

    return wrapper
