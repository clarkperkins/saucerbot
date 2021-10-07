# -*- coding: utf-8 -*-

from typing import Any

import requests
from asgiref.sync import sync_to_async
from django.conf import settings
from django.urls import reverse

API_ENDPOINT = "https://discord.com/api/v8"


def get_redirect_uri() -> str:
    return f"https://{settings.SERVER_DOMAIN}{reverse('discord:oauth')}"


def _token_request(**kwargs) -> dict[str, Any]:
    data = kwargs
    data["client_id"] = settings.DISCORD_CLIENT_ID
    data["client_secret"] = settings.DISCORD_CLIENT_SECRET

    print(data)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def exchange_code(code: str) -> dict[str, Any]:
    return _token_request(
        grant_type="authorization_code",
        code=code,
        redirect_uri=get_redirect_uri(),
    )


def refresh_token(token: str) -> dict[str, Any]:
    return _token_request(
        grant_type="refresh_token",
        refresh_token=token,
    )
