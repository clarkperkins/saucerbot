# -*- coding: utf-8 -*-

import dj_database_url

SECRET_KEY = 'abcdef123456'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Don't require SSL for test
DATABASES = {
    'default': dj_database_url.config(default='sqlite://:memory:', conn_max_age=600),
}
