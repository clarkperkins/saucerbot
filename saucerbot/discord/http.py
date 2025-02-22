# -*- coding: utf-8 -*-

import asyncio

import aiohttp
from discord.errors import HTTPException, LoginFailure
from discord.gateway import DiscordClientWebSocketResponse
from discord.http import HTTPClient, Route
from discord.types import user
from discord.user import MISSING


class SaucerbotDiscordHTTPClient(HTTPClient):

    async def user_login(self, token_type: str, access_token: str) -> user.User:
        # Necessary to get aiohttp to stop complaining about session creation
        if self.connector is MISSING:
            self.connector = aiohttp.TCPConnector(limit=0)

        self.__dict__["_HTTPClient__session"] = aiohttp.ClientSession(
            connector=self.connector,
            ws_response_class=DiscordClientWebSocketResponse,
            trace_configs=None if self.http_trace is None else [self.http_trace],
            cookie_jar=aiohttp.DummyCookieJar(),
            headers={"Authorization": f"{token_type} {access_token}"},
        )
        self._global_over = asyncio.Event()
        self._global_over.set()

        try:
            data = await self.request(Route("GET", "/users/@me"))
        except HTTPException as exc:
            if exc.status == 401:
                raise LoginFailure("Improper token has been passed.") from exc
            raise

        return data
