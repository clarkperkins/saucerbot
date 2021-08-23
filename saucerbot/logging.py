# -*- coding: utf-8 -*-

from datetime import datetime
from logging import LogRecord
from typing import Optional

from colorlog import ColoredFormatter


class HighlightingFormatter(ColoredFormatter):
    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        dt = datetime.fromtimestamp(record.created).astimezone()
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            t = dt.strftime(self.default_time_format)
            if self.default_msec_format:
                s = self.default_msec_format % (t, record.msecs)
            else:
                s = '%s,%03d' % (t, record.msecs)
        return s
