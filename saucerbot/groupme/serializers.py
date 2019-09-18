# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, Union

from lowerpines.endpoints.group import Group
from lowerpines.exceptions import NoneFoundException
from rest_framework import serializers

from saucerbot.groupme.handlers import registry, Handler as RHandler
from saucerbot.groupme.models import Bot, Handler, User

logger = logging.getLogger(__name__)


class HandlerSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(view_name='groupme:handler-detail',
                                               lookup_field='name')
    name = serializers.CharField()
    description = serializers.CharField()
    regexes = serializers.ListField(child=serializers.CharField())

    def create(self, validated_data):
        raise NotImplementedError("Read-only serializer")

    def update(self, instance, validated_data):
        raise NotImplementedError("Read-only serializer")


class HandlerRelatedField(serializers.RelatedField):
    """
    This field is kind of weird - it's able to handle both the Handler objects
    that are in the registry, along with the Handler model objects.
    """
    queryset = registry

    def to_internal_value(self, data: str) -> RHandler:
        """
        This returns the registry handler associated with the given name
        """
        handler = self.get_queryset().get(name=data)
        if not handler:
            raise serializers.ValidationError(f"Handler with name '{data}' doesn't exist")
        return handler

    def to_representation(self, value: Union[Handler, RHandler]) -> str:
        """
        Can deal with both registry handlers and handler model objects
        """
        if isinstance(value, RHandler):
            return value.name
        else:
            return value.handler_name


class GroupRelatedField(serializers.RelatedField):

    def get_queryset(self):
        user: User = self.context['request'].user
        return user.gmi.groups

    def to_internal_value(self, data: str) -> Group:
        try:
            return self.get_queryset().get(group_id=data)
        except NoneFoundException:
            raise serializers.ValidationError(f"Group with id '{data}' doesn't exist")

    def to_representation(self, value: Group) -> str:
        return value.group_id


class BotSerializer(serializers.HyperlinkedModelSerializer):
    group = GroupRelatedField()
    avatar_url = serializers.URLField(write_only=True, label='Avatar URL', allow_null=True,
                                      required=False, default=None)
    handlers = HandlerRelatedField(many=True, required=False, default=[])

    class Meta:
        model = Bot
        fields = ['url', 'name', 'slug', 'group', 'avatar_url', 'handlers']
        extra_kwargs = {
            'url': {'lookup_field': 'slug', 'view_name': 'groupme:bot-detail'},
        }

    def create(self, validated_data: Dict[str, Any]) -> Bot:
        handlers = validated_data.pop('handlers')

        bot = super().create(validated_data)

        # Create all the handler instances
        handler_objects = []
        for handler in handlers:
            handler_objects.append(Handler(bot=bot, handler_name=handler.name))

        Handler.objects.bulk_create(handler_objects)

        return bot

    def validate_group(self, group: Group):
        # Make sure the group doesn't change
        if self.instance:
            if group and self.instance.group_id != group.group_id:
                raise serializers.ValidationError("Group may not be changed")
            # just skip this field, no need to change it
            raise serializers.SkipField()
        return group

    def update(self, instance: Bot, validated_data: Dict[str, Any]) -> Bot:
        handlers = validated_data.pop('handlers', None)

        bot = super().update(instance, validated_data)

        if handlers:
            new_handler_set = set(h.name for h in handlers)
            current_handler_set = set(h.handler_name for h in bot.handlers.all())

            # Delete the removed ones
            removed_handlers = current_handler_set - new_handler_set
            bot.handlers.filter(handler_name__in=removed_handlers).delete()

            # Create the new ones
            handlers_to_create = new_handler_set - current_handler_set
            handler_objects = []
            for handler in handlers_to_create:
                handler_objects.append(Handler(bot=bot, handler_name=handler))

            Handler.objects.bulk_create(handler_objects)

        return bot
