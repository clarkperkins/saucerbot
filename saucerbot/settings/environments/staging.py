# -*- coding: utf-8 -*-

import os

from saucerbot.settings.base import HEROKU_APP_NAME

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Only do the redirect if we actually have an app name to redirect to
if HEROKU_APP_NAME:
    SECURE_SSL_REDIRECT = True
    SECURE_SSL_HOST = f'{HEROKU_APP_NAME}.herokuapp.com'
