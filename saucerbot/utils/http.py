# -*- coding: utf-8 -*-

"""
Shared HTTP settings for the outbound calls saucerbot makes.

Every one of these runs somewhere a hang is expensive: the discord worker makes
them from inside its event loop, so a request that never returns stops the bot
from handling messages at all, with the pod still looking healthy.  requests
has no default timeout, so one has to be passed explicitly every time.
"""

# (connect, read) in seconds.  Connecting should be near instant to anything we
# talk to; reads get more room since we scrape a few slow pages.
DEFAULT_TIMEOUT = (5, 15)
