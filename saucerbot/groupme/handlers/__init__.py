# -*- coding: utf-8 -*-

import inspect
import re
from collections.abc import Callable, Sequence
from typing import Any, NamedTuple, Optional, Union

from lowerpines.endpoints.bot import Bot
from lowerpines.endpoints.message import Message
from scout_apm.api import instrument


class Handler(NamedTuple):
    name: str
    regexes: Optional[list[re.Pattern[str]]]
    func: Callable
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
        self, bot: Bot, message: Message, regexes: list[re.Pattern]
    ) -> bool:
        for regex in regexes:
            with instrument("Regex", tags={"regex": regex.pattern}):
                match = regex.search(message.text)
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
                    self.func(bot, **kwargs)
                return True

        # Nothing matched
        return False

    def run(self, bot: Bot, message: Message) -> bool:
        if self.regexes:
            # This is a regex handler, special case
            return self.handle_regexes(bot, message, self.regexes)
        else:
            # Just a plain handler.
            # If it returns something truthy, it matched, so it means we should stop
            with instrument("Handler", tags={"name": self.name}):
                return self.func(bot, message)


class HandlerRegistry(Sequence[Handler]):
    def __init__(self):
        self.handlers: list[Handler] = []

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

    # get() method to make this look like a django queryset
    def get(self, **kwargs) -> Optional[Handler]:
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
        regex: Union[str, list[str]] = None,
        *,
        name: str = None,
        case_sensitive: bool = False,
        always_run: bool = False,
    ) -> Callable:
        """
        Add a message handler
        """
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
                    func,
                    always_run,
                )
            )
            return func

        return wrapper


# Create the registry
registry = HandlerRegistry()
