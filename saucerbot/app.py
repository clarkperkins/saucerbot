# -*- coding: utf-8 -*-

from flask import Flask


class SaucerFlask(Flask):

    def __init__(self, *args, **kwargs):
        super(SaucerFlask, self).__init__(*args, **kwargs)
        self.handlers = set()

    def handler(self, *args, **kwargs):
        """
        Add a message handler
        """
        def wrapper(func):
            self.handlers.add(func)
            return func

        return wrapper
