# -*- coding: utf-8 -*-

from typing import Dict, Union

from django.conf import settings
from lowerpines.endpoints import bot, group
from lowerpines.gmi import GMI
from lowerpines.message import ComplexMessage

# Create our caches
__global_gmis: Dict[str, GMI] = {}
__global_bots: Dict[str, bot.Bot] = {}
__global_groups: Dict[str, group.Group] = {}


def get_gmi() -> GMI:
    api_key = settings.GROUPME_API_KEY
    if api_key not in __global_gmis:
        __global_gmis[api_key] = GMI(api_key)

    return __global_gmis[api_key]


def get_bot() -> bot.Bot:
    bot_id = settings.GROUPME_BOT_ID
    if bot_id not in __global_bots:
        __global_bots[bot_id] = get_gmi().bots.get(bot_id=bot_id)

    return __global_bots[bot_id]


def get_group() -> group.Group:
    bot_id = settings.GROUPME_BOT_ID
    if bot_id not in __global_groups:
        __global_groups[bot_id] = get_bot().group

    return __global_groups[bot_id]


def post_message(message: Union[str, ComplexMessage]) -> None:
    get_bot().post(message)
