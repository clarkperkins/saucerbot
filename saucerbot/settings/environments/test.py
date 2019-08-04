# -*- coding: utf-8 -*-

from typing import Optional

import dj_database_url

SECRET_KEY = 'abcdef123456'

DEBUG = True

ALLOWED_HOSTS = ['*']

GROUPME_API_KEY: Optional[str] = '123456'
GROUPME_BOT_ID: Optional[str] = '123456'

# Don't require SSL for test
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600),
}
