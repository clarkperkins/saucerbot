# -*- coding: utf-8 -*-
from typing import Any

from discord import Member
from discord.abc import GuildChannel
from discord.http import HTTPClient, Route
from discord.mixins import Hashable
from discord.state import ConnectionState
from django.conf import settings


class SaucerbotConnectionState(ConnectionState):
    def parse_interaction_create(self, data):
        channel, _ = self._get_guild_channel(data)
        interaction = Interaction(channel=channel, data=data, state=self)
        self.dispatch("interaction", interaction)


class Interaction(Hashable):
    def __init__(
        self,
        *,
        state: SaucerbotConnectionState,
        channel: GuildChannel,
        data: dict[str, Any],
    ):
        self._state = state
        self.id = int(data["id"])
        self.application_id = data.get("application_id")
        self.channel = channel
        self.type = data["type"]
        self.token = data["token"]
        self.data = data["data"]
        self.member = Member(data=data["member"], guild=channel.guild, state=state)  # type: ignore

    async def respond(self, content: str):
        await self._state.http.respond_interaction(self.id, self.token, content)  # type: ignore

    async def follow_up(self, content: str):
        await self._state.http.follow_up_interaction(self.token, content)  # type: ignore


class RouteV8(Route):
    BASE = "https://discord.com/api/v8"


class SaucerbotHTTPClient(HTTPClient):
    def respond_interaction(
        self, interaction_id: int, interaction_token: str, content: str
    ):
        r = RouteV8(
            "POST",
            "/interactions/{interaction_id}/{interaction_token}/callback",
            interaction_id=interaction_id,
            interaction_token=interaction_token,
        )
        data = {}

        if content:
            data["content"] = content

        payload = {
            "type": 4,
            "data": data,
        }

        return self.request(r, json=payload)

    def follow_up_interaction(self, interaction_token: str, content: str):
        r = RouteV8(
            "POST",
            "/webhooks/{application_id}/{interaction_token}",
            application_id=settings.DISCORD_APPLICATION_ID,
            interaction_token=interaction_token,
        )
        payload = {}

        if content:
            payload["content"] = content

        return self.request(r, json=payload)
