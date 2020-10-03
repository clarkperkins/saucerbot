# -*- coding: utf-8 -*-

import yaml

from saucerbot.settings.base import BASE_DIR

# Configure logging from the yaml file, if it exists
LOGGING_CONF_FILE = BASE_DIR / 'logging.yaml'

if LOGGING_CONF_FILE.is_file():
    with LOGGING_CONF_FILE.open('rt', encoding='utf8') as f:
        LOGGING = yaml.safe_load(f)
