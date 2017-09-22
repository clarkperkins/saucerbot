# -*- coding: utf-8 -*-

import typing

from groupy import config
from groupy.object.attachments import (
    Image,
    Location,
    Emoji as GroupyEmoji,
    Mentions,
    Split,
)

__all__ = ['Image', 'Location', 'Emoji', 'Mentions', 'Split']


class Emoji(GroupyEmoji):

    def __init__(self, charmap: typing.List[typing.List[int]]) -> None:
        super(Emoji, self).__init__(config.EMOJI_PLACEHOLDER, charmap)
