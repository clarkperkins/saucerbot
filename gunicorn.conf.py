# -*- coding: utf-8 -*-

from gunicorn.glogging import Logger

from saucerbot.logging import HighlightingFormatter


class GunicornLogger(Logger):
    error_fmt = r"[%(asctime)s] [%(process)d] %(log_color)s[%(levelname)s]%(reset)s %(message)s"
    datefmt = r"%Y-%m-%d %H:%M:%S.%f%z"

    def setup(self, cfg):
        super().setup(cfg)
        h = self._get_gunicorn_handler(self.error_log)
        h.setFormatter(HighlightingFormatter(self.error_fmt, self.datefmt, reset=False))


logger_class = GunicornLogger
