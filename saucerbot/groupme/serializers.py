# -*- coding: utf-8 -*-

import logging

from collections import OrderedDict
from lowerpines.exceptions import NoneFoundException
from rest_framework import serializers

from saucerbot.groupme.handlers import registry
from saucerbot.groupme.models import Bot

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
    queryset = registry

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serializer = HandlerSerializer()

    def to_internal_value(self, data):
        return registry.get(name=data)

    def to_representation(self, value):
        return value.handler_name

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                item.name,
                self.display_value(item)
            )
            for item in queryset
        ])


class BotSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.CharField(write_only=True)
    avatar_url = serializers.URLField(write_only=True, label='Avatar URL', allow_null=True)
    handlers = HandlerRelatedField(many=True)

    class Meta:
        model = Bot
        fields = ['url', 'name', 'slug', 'group', 'avatar_url', 'handlers']
        extra_kwargs = {
            'url': {'lookup_field': 'slug', 'view_name': 'groupme:bot-detail'},
        }

    def get_fields(self):
        fields = super().get_fields()

        if self.instance:
            del fields['group']

        return fields

    def validate(self, attrs):
        group_id = attrs.pop('group')

        if group_id:
            user_info = self.context['request'].auth
            try:
                attrs['group'] = user_info.gmi.groups.get(group_id=group_id)
            except NoneFoundException:
                raise serializers.ValidationError({
                    'group': f"Group with id '{group_id}' doesn't exist"
                })

        return attrs

    def create(self, validated_data):
        handlers = validated_data.pop('handlers')

        bot = super().create(validated_data)

        # Create all the handler instances
        for handler in handlers:
            bot.handlers.create(handler_name=handler.name)

        return bot
