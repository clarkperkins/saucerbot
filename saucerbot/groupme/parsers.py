# -*- coding: utf-8 -*-


import json
import logging

from django.http.request import HttpRequest
from lowerpines.message import Message
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser

from saucerbot.groupme.utils import get_gmi

logger = logging.getLogger(__name__)


class GroupMeMessageParser(JSONParser):

    def parse(self, stream: HttpRequest,
              media_type: str = None,
              parser_context: str = None) -> Message:
        parsed_content = super().parse(stream, media_type, parser_context)
        logger.info('Received raw message: {}'.format(json.dumps(parsed_content)))

        # Load it as a groupme message
        try:
            return Message.from_json(get_gmi(), parsed_content)
        except Exception as e:
            raise ParseError(f'Failed to load message as groupme message - {e}')
