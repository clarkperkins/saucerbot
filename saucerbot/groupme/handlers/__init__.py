# -*- coding: utf-8 -*-

import re
from typing import Callable, List, NamedTuple, Optional, Pattern, Sequence, Union


class Handler(NamedTuple):
    name: str
    regexes: Optional[List[Pattern[str]]]
    func: Callable

    @property
    def description(self):
        doc = self.func.__doc__
        return doc.strip() if doc else None

    def __str__(self):
        ret = self.name
        if self.description:
            ret += f' - {self.description}'
        return ret


class HandlerRegistry(Sequence[Handler]):

    def __init__(self):
        self.handlers: List[Handler] = []

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
    # pylint: disable=unused-argument
    def get(self, *args, **kwargs) -> Optional[Handler]:
        for handler in self.handlers:
            match = True
            for k, v in kwargs.items():
                if getattr(handler, k) != v:
                    match = False
                    break

            if match:
                return handler

        return None

    def handler(self, regex: Union[str, List[str]] = None, name: str = None,
                case_sensitive: bool = False) -> Callable:
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

            self.handlers.append(Handler(
                name or func.__name__,
                [re.compile(r, flags) for r in regexes],
                func,
            ))
            return func

        return wrapper


# Create the registry
registry = HandlerRegistry()
