# -*- coding: utf-8 -*-

import os

from saucerbot.settings.base import HEROKU_APP_DOMAIN

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SERVER_DOMAIN = "saucerbot.clarkperkins.com"

ALLOWED_HOSTS = [SERVER_DOMAIN]

SECURE_SSL_REDIRECT = True
SECURE_SSL_HOST = SERVER_DOMAIN

# Only add the heroku domain if we have it
if HEROKU_APP_DOMAIN:
    ALLOWED_HOSTS.append(HEROKU_APP_DOMAIN)
