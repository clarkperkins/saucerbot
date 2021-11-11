# -*- coding: utf-8 -*-

import logging
from typing import Any

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.reverse import reverse

from saucerbot.core.serializers import HandlerRelatedField
from saucerbot.discord.models import Channel, Guild, Handler

logger = logging.getLogger(__name__)


class ChannelHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    # pylint: disable=redefined-builtin
    def get_url(  # type: ignore[override]
        self, obj: Channel, view_name: str, request: Request, format: str
    ):
        url_kwargs = {
            "guild_id": obj.guild.guild_id,
            "channel_id": obj.channel_id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    # The DRF mypy plugin has the typing wrong for this method.
    # Se when we add type hints mypy fails.
    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = {
            "guild__guild_id": view_kwargs["guild_id"],
            "channel_id": view_kwargs["channel_id"],
        }
        return self.get_queryset().get(**lookup_kwargs)


class GuildSerializer(serializers.HyperlinkedModelSerializer):
    channels = serializers.HyperlinkedIdentityField(
        view_name="discord:channel-list",
        lookup_field="guild_id",
        lookup_url_kwarg="guild_id",
        read_only=True,
    )

    class Meta:
        model = Guild
        fields = ["url", "guild_id", "name", "channels"]
        extra_kwargs = {
            "url": {"view_name": "discord:guild-detail", "lookup_field": "guild_id"},
        }


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    url = ChannelHyperlinkedIdentityField(view_name="discord:channel-detail")
    handlers = HandlerRelatedField(
        platform="discord", many=True, required=False, default=[]
    )

    class Meta:
        model = Channel
        fields = ["url", "channel_id", "name", "handlers"]
        extra_kwargs = {
            "channel_id": {"read_only": True},
            "name": {"read_only": True},
        }

    def update(self, instance: Channel, validated_data: dict[str, Any]) -> Channel:
        handlers = validated_data.pop("handlers", None)

        channel = super().update(instance, validated_data)

        if handlers:
            new_handler_set = set(h.name for h in handlers)
            current_handler_set = set(h.handler_name for h in channel.handlers.all())

            # Delete the removed ones
            removed_handlers = current_handler_set - new_handler_set
            channel.handlers.filter(handler_name__in=removed_handlers).delete()

            # Create the new ones
            handlers_to_create = new_handler_set - current_handler_set
            handler_objects = []
            for handler in handlers_to_create:
                handler_objects.append(Handler(channel=channel, handler_name=handler))

            Handler.objects.bulk_create(handler_objects)

        return channel
