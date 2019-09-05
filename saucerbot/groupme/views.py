# -*- coding: utf-8 -*-

import json
import logging

from django.conf import settings
from django.urls import reverse
from django.views.generic import RedirectView
from lowerpines.message import Message
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from saucerbot.groupme.authentication import UserInfoAuthentication, USER_INFO
from saucerbot.groupme.handlers import registry
from saucerbot.groupme.models import Bot, UserInfo
from saucerbot.groupme.permissions import HasUserInfo
from saucerbot.groupme.serializers import BotSerializer, HandlerSerializer
from saucerbot.utils import did_the_dores_win

logger = logging.getLogger(__name__)


class LoginRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        if USER_INFO in self.request.session:
            return reverse('groupme:bot-list')
        else:
            return 'https://oauth.groupme.com/oauth/authorize' \
                   f'?client_id={settings.GROUPME_CLIENT_ID}'


class OAuthView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        access_token = self.request.GET['access_token']

        info = UserInfo.objects.from_token(access_token)

        # Make sure we have a session
        if self.request.session.session_key is None:
            logger.info("Generating new session")
            self.request.session.cycle_key()

        self.request.session[USER_INFO] = str(info.id)

        return reverse('groupme:bot-list', *args, **kwargs)


class BotViewSet(ModelViewSet):
    serializer_class = BotSerializer
    lookup_field = 'slug'
    lookup_value_type = 'str'
    authentication_classes = [UserInfoAuthentication]
    permission_classes = [HasUserInfo]

    def get_queryset(self):
        return Bot.objects.filter(user_info=self.request.auth)

    def perform_create(self, serializer: BotSerializer):
        serializer.save(user_info=self.request.auth)


class BotActionsViewSet(GenericViewSet):
    serializer_class = BotSerializer
    lookup_field = 'slug'
    lookup_value_type = 'str'
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Bot.objects.all()

    def parse_as_message(self, bot: Bot) -> Message:
        if logger.isEnabledFor(logging.INFO):
            raw_json = json.dumps(self.request.data)
            logger.info(f'Received raw message: {raw_json}')

        # Load it as a groupme message
        try:
            return Message.from_json(bot.user_info.gmi, self.request.data)
        except Exception:
            raise ParseError('Invalid GroupMe message')

    @action(methods=['post'], detail=True)
    def callback(self, request: Request, *args, **kwargs) -> Response:
        bot = self.get_object()
        message = self.parse_as_message(bot)

        if not message:
            raise ParseError('Invalid GroupMe message')

        response = {
            'message_sent': bot.handle_message(message),
        }

        return Response(response)

    @action(methods=['post'], detail=True, url_path='dores-win')
    def dores_win(self, request: Request, *args, **kwargs) -> Response:
        bot = self.get_object()
        result = did_the_dores_win(False, False)
        if result:
            bot.post_message(result)
        response = {
            'ok': True,
            'win': result is not None,
            'result': result
        }
        return Response(response)


class HandlerViewSet(ReadOnlyModelViewSet):
    serializer_class = HandlerSerializer
    lookup_field = 'name'
    lookup_value_type = 'str'
    authentication_classes = [UserInfoAuthentication]
    permission_classes = [HasUserInfo]

    def get_queryset(self):
        return registry
