# -*- coding: utf-8 -*-

import io
import os

import yaml

from saucerbot.settings.base import BASE_DIR

# Configure logging from the yaml file, if it exists
LOGGING_CONF_FILE = os.path.join(BASE_DIR, 'logging.yaml')

if os.path.isfile(LOGGING_CONF_FILE):
    with io.open(LOGGING_CONF_FILE, 'rt', encoding='utf8') as f:
        LOGGING = yaml.safe_load(f)
