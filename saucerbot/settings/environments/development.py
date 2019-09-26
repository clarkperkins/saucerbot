# -*- coding: utf-8 -*-

import dj_database_url

SECRET_KEY = 'abcdef123456'

DEBUG = True

SERVER_DOMAIN = 'localhost'

ALLOWED_HOSTS = ['*']

# Don't require SSL for dev
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600),
}
