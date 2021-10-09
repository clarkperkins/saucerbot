# -*- coding: utf-8 -*-

import logging
from typing import Union, cast

from django.db.models import QuerySet
from rest_framework import serializers

from saucerbot.groupme.models import Handler
from saucerbot.handlers import Handler as RHandler
from saucerbot.handlers import registry

logger = logging.getLogger(__name__)


class HandlerSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="core:handler-detail", lookup_field="name"
    )
    name = serializers.CharField()
    description = serializers.CharField()
    platforms = serializers.ListField(child=serializers.CharField())
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

    def __init__(self, platform: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = platform

    def get_queryset(self) -> QuerySet:
        return cast(QuerySet, registry.filter(platform=self.platform))

    def to_internal_value(self, data: str) -> RHandler:
        """
        This returns the registry handler associated with the given name
        """
        handler = self.get_queryset().get(name=data)
        if not handler:
            raise serializers.ValidationError(
                f"Handler with name '{data}' doesn't exist"
            )
        return handler

    def to_representation(self, value: Union[Handler, RHandler]) -> str:
        """
        Can deal with both registry handlers and handler model objects
        """
        if isinstance(value, RHandler):
            return value.name
        else:
            return value.handler_name
