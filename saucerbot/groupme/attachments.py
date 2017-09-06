# -*- coding: utf-8 -*-

from groupy import config
from groupy.object.attachments import *
from groupy.object.attachments import Emoji as GroupyEmoji

__all__ = ['Image', 'Location', 'Emoji', 'Mentions', 'Split']


class Emoji(GroupyEmoji):

    def __init__(self, charmap):
        super(Emoji, self).__init__(config.EMOJI_PLACEHOLDER, charmap)
