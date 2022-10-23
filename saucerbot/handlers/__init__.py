# -*- coding: utf-8 -*-

import inspect
import logging
import re
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from importlib import import_module
from typing import Any, NamedTuple

from arrow import Arrow
from scout_apm.api import instrument

logger = logging.getLogger(__name__)

VALID_PLATFORMS = {"discord", "groupme"}


class BotContext(metaclass=ABCMeta):
    @abstractmethod
    def post(self, message: Any):
        raise NotImplementedError()


class Message(metaclass=ABCMeta):
    @property
    @abstractmethod
    def user_id(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def user_name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def content(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def created_at(self) -> Arrow:
        """
        In UTC
        """
        raise NotImplementedError


class Handler(NamedTuple):
    name: str
    regexes: list[re.Pattern[str]] | None
    platforms: set[str]
    func: Callable
    on_by_default: bool
    always_run: bool

    @property
    def description(self):
        doc = self.func.__doc__
        return doc.strip() if doc else None

    def __str__(self):
        ret = self.name
        if self.description:
            ret += f" - {self.description}"
        return ret

    def handle_regexes(
        self, context: BotContext, message: Message, regexes: list[re.Pattern]
    ) -> bool:
        for regex in regexes:
            with instrument("Regex", tags={"regex": regex.pattern}):
                match = regex.search(message.content)
            if match:
                # We matched!  Now call our handler and break out of the loop

                # We want to see what arguments our function takes, though.
                sig = inspect.signature(self.func)

                kwargs: dict[str, Any] = {}
                if "message" in sig.parameters:
                    kwargs["message"] = message
                if "match" in sig.parameters:
                    kwargs["match"] = match

                with instrument("Handler", tags={"name": self.name}):
                    self.func(context, **kwargs)
                return True

        # Nothing matched
        return False

    def run(self, context: BotContext, message: Message) -> bool:
        if self.regexes:
            # This is a regex handler, special case
            return self.handle_regexes(context, message, self.regexes)
        else:
            # Just a plain handler.
            # If it returns something truthy, it matched, so it means we should stop
            with instrument("Handler", tags={"name": self.name}):
                return self.func(context, message)


class HandlerRegistry(Sequence[Handler]):
    def __init__(self, handlers: list[Handler] = None, loaded_modules: set[str] = None):
        self.handlers: list[Handler] = handlers or []
        self._loaded_modules: set[str] = loaded_modules or set()

    # Sequence methods that just delegate to the underlying list
    def __getitem__(self, item):
        return self.handlers[item]

    def __len__(self):
        return len(self.handlers)

    def __contains__(self, item):
        return item in self.handlers

    def __iter__(self):
        return iter(self.handlers)

    def __reversed__(self):
        return reversed(self.handlers)

    # End delegate methods

    def initialize(self, handler_modules: Iterable[str]):
        initial_handler_count = len(self)

        # Import the handler modules
        for handler_module in handler_modules:
            if handler_module in self._loaded_modules:
                logger.debug("Already loaded %s", handler_module)
            else:
                start_handlers = len(self)
                import_module(handler_module)
                logger.info(
                    "Loaded %s handlers from %s",
                    len(self) - start_handlers,
                    handler_module,
                )
                self._loaded_modules.add(handler_module)

        total_handlers = len(self)

        logger.info(
            "Loaded %s new handlers, %s handlers total",
            total_handlers - initial_handler_count,
            total_handlers,
        )

    # filter method to only get handlers for a specific platform
    def filter(self, platform: str) -> "HandlerRegistry":
        filtered = [h for h in self.handlers if platform in h.platforms]
        return HandlerRegistry(filtered, self._loaded_modules)

    # get() method to make this look like a django queryset
    def get(self, **kwargs) -> Handler | None:
        for handler in self.handlers:
            match = True
            for k, v in kwargs.items():
                if getattr(handler, k) != v:
                    match = False
                    break

            if match:
                return handler

        return None

    def handler(
        self,
        regex: str | list[str] | None = None,
        *,
        name: str = None,
        case_sensitive: bool = False,
        platforms: Iterable[str] | None = None,
        on_by_default: bool = False,
        always_run: bool = False,
    ) -> Callable:
        """
        Add a message handler
        """
        if platforms:
            platforms = {p.lower() for p in platforms}
            invalid_platforms = platforms - VALID_PLATFORMS
            if invalid_platforms:
                raise ValueError(f"Invalid platforms: {invalid_platforms}")

        regexes = regex or []
        if isinstance(regex, str):
            regexes = [regex]
        elif regex and not isinstance(regex, list):
            regexes = list(regex)

        def wrapper(func: Callable) -> Callable:
            flags = 0

            if not case_sensitive:
                flags = flags | re.IGNORECASE

            self.handlers.append(
                Handler(
                    name or func.__name__,
                    [re.compile(r, flags) for r in regexes],
                    set(platforms or VALID_PLATFORMS),
                    func,
                    on_by_default,
                    always_run,
                )
            )
            return func

        return wrapper

    def handle_message(
        self,
        platform: str,
        handler_names: set[str],
        context: BotContext,
        message: Message,
    ) -> list[str]:
        matched_handlers: list[str] = []

        for handler in self:
            if platform not in handler.platforms:
                continue

            if handler.name not in handler_names:
                continue

            # We already matched at least one handler, don't run this one
            if matched_handlers and not handler.always_run:
                continue

            logger.debug("Trying message handler %s ...", handler.name)

            matched = handler.run(context, message)

            # Keep track of the handlers that matched
            if matched:
                matched_handlers.append(handler.name)

        return matched_handlers


# Create the registry
registry = HandlerRegistry()
