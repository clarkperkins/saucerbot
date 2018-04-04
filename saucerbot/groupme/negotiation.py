# -*- coding: utf-8 -*-

from typing import List, Optional

from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.parsers import BaseParser
from rest_framework.request import Request

from saucerbot.groupme.parsers import GroupMeMessageParser


class GroupMeCallbackNegotiation(DefaultContentNegotiation):

    def select_parser(self, request: Request, parsers: List[BaseParser]) -> Optional[BaseParser]:
        # Try the default first
        default_parser = super().select_parser(request, parsers)

        # If one was already selected, just return it
        if default_parser:
            return default_parser

        # Otherwise look for a groupme parser
        for parser in parsers:
            if isinstance(parser, GroupMeMessageParser):
                return parser

        # We still found nothing
        return None
