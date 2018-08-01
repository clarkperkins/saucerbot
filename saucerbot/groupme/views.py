# -*- coding: utf-8 -*-

import inspect
import logging

from lowerpines.message import Message
from rest_framework.exceptions import ParseError
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from saucerbot.groupme.handlers import registry
from saucerbot.groupme.negotiation import GroupMeCallbackNegotiation
from saucerbot.groupme.parsers import GroupMeMessageParser
from saucerbot.groupme.utils import post_message
from saucerbot.utils import did_the_dores_win

logger = logging.getLogger(__name__)


class GroupMeCallbacks(APIView):
    parser_classes = [GroupMeMessageParser]
    renderer_classes = [JSONRenderer]
    content_negotiation_class = GroupMeCallbackNegotiation

    # pylint: disable=no-self-use
    def post(self, request: Request, name: str, **kwargs) -> Response:
        # Specify the type of our message for type checking
        message: Message = request.data

        if not message:
            raise ParseError('Invalid GroupMe message')

        # We don't want to accidentally respond to ourself
        if message.sender_type == 'bot' and name in message.name:
            return Response({'message_sent': False})

        message_sent = False

        # Call all our handlers
        for handler in registry:
            logger.debug(f"Trying message handler {handler.func.__name__} ...")

            if handler.regex:
                # This is a regex handler, special case
                match = handler.regex.search(message.text)
                if match:
                    # We matched!  Now call our handler and break out of the loop

                    # We want to see what arguments our function takes, though.
                    sig = inspect.signature(handler.func)

                    kwargs = {}
                    if 'message' in sig.parameters:
                        kwargs['message'] = message
                    if 'match' in sig.parameters:
                        kwargs['match'] = match

                    handler.func(**kwargs)
                    message_sent = True
                    break
            else:
                # Just a plain handler.
                # If it returns something truthy, it matched, so it means we should stop
                if handler.func(message):
                    message_sent = True
                    break

        response = {
            'message_sent': message_sent,
        }

        return Response(response)


class DoresWinCallback(APIView):

    # pylint: disable=no-self-use
    def post(self, request: Request, **kwargs) -> Response:
        result = did_the_dores_win(False, False)
        if result:
            post_message(result)
        response = {
            'ok': True,
            'win': result is not None,
            'result': result
        }
        return Response(response)
