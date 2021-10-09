# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict

from django.urls import NoReverseMatch, path
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import APIRootView, DefaultRouter, DynamicRoute, Route
from rest_framework.urlpatterns import format_suffix_patterns

logger = logging.getLogger(__name__)


class SaucerbotAPIRootView(APIRootView):
    name = "API Root"

    def get(self, request, *args, **kwargs):
        # Return a plain {"name": "hyperlink"} response.
        ret = OrderedDict()
        namespace = request.resolver_match.namespace

        def try_add(_key: str, _url_name: str):
            try:
                ret[_key] = reverse(
                    _url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                    format=kwargs.get("format", None),
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                pass

        for key, url_name in self.api_root_dict.items():
            try_add(key, url_name)
            if namespace:
                try_add(key, namespace + ":" + url_name)

        return Response(ret)


class PathRouter(DefaultRouter):
    APIRootView = SaucerbotAPIRootView

    routes = [
        # List route.
        Route(
            url="{prefix}{trailing_slash}",
            mapping={"get": "list", "post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        DynamicRoute(
            url="{prefix}/{url_path}{trailing_slash}",
            name="{basename}-{url_name}",
            detail=False,
            initkwargs={},
        ),
        # Detail route.
        Route(
            url="{prefix}/{lookup}{trailing_slash}",
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            },
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        DynamicRoute(
            url="{prefix}/{lookup}/{url_path}{trailing_slash}",
            name="{basename}-{url_name}",
            detail=True,
            initkwargs={},
        ),
    ]

    def __init__(self, *args, **kwargs):
        self.api_root_name = kwargs.pop("api_root_name", "API Root")
        self.api_root_authentication_class = kwargs.pop(
            "api_root_authentication_class", None
        )
        self.extra_api_root_paths = kwargs.pop("extra_api_root_paths", None)
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_lookup_path(viewset, lookup_prefix: str = "") -> str:
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        base_path = "<{lookup_value}:{lookup_prefix}{lookup_url_kwarg}>"
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = getattr(viewset, "lookup_field", "pk")
        lookup_url_kwarg = getattr(viewset, "lookup_url_kwarg", None) or lookup_field
        lookup_value = getattr(viewset, "lookup_value_type", "int")
        return base_path.format(
            lookup_prefix=lookup_prefix,
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value,
        )

    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        urls = []

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_path(viewset)
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                path_str = route.url.format(
                    prefix=prefix, lookup=lookup, trailing_slash=self.trailing_slash
                )

                # If there is no prefix, the first part of the url is probably
                #   controlled by project's urls.py and the router is in an app,
                #   so a slash in the beginning will (A) cause Django to give
                #   warnings and (B) generate URLS that will require using '//'.
                # if not prefix and path_str[:2] == '^/':
                #     regex = '^' + path_str[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update(
                    {
                        "basename": basename,
                        "detail": route.detail,
                    }
                )

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename)
                urls.append(path(path_str, view, name=name))

        if self.include_root_view:
            view = self.get_api_root_view(api_urls=urls)
            root_url = path("", view, name=self.root_view_name)
            urls.append(root_url)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls

    def get_api_root_view(self, api_urls=None):
        """
        Return a basic root view.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, _, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        if self.extra_api_root_paths:
            api_root_dict.update(self.extra_api_root_paths)

        view_kwargs = {
            "name": self.api_root_name,
            "api_root_dict": api_root_dict,
        }

        if self.api_root_authentication_class:
            view_kwargs["authentication_classes"] = [self.api_root_authentication_class]

        return self.APIRootView.as_view(**view_kwargs)
