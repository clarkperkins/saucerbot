# -*- coding: utf-8 -*-

from datetime import datetime
from logging import LogRecord

from colorlog import ColoredFormatter

_MSEC_FORMAT = "%s,%03d"


class HighlightingFormatter(ColoredFormatter):
    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created).astimezone()
        if datefmt:
            s = dt.strftime(datefmt)
        else:  # pragma: no cover
            t = dt.strftime(self.default_time_format)
            if self.default_msec_format:
                s = self.default_msec_format % (t, record.msecs)
            else:
                s = _MSEC_FORMAT % (t, record.msecs)
        return s
