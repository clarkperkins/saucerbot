# -*- coding: utf-8 -*-

import os

from groupy import config
from groupy.object.listers import FilterList
from groupy.object.responses import User, Member

from saucerbot.groupme import attachments
from saucerbot.groupme.custom import Bot, Group

# Set the API key
config.API_KEY = os.environ['GROUPME_API_KEY']

# Set the emoji placeholder
EMOJI_PLACEHOLDER = '\ufffd'
config.EMOJI_PLACEHOLDER = EMOJI_PLACEHOLDER

__all__ = ['Bot', 'Group', 'Member', 'User', 'FilterList', 'attachments']
