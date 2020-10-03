# -*- coding: utf-8 -*-

import os

from saucerbot.settings.base import HEROKU_APP_NAME

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = f'[{HEROKU_APP_NAME}] '

SERVER_EMAIL = 'noreply@clarkperkins.com'

ADMINS = [
    ('Saucerbot Admin', os.environ.get('ADMIN_EMAIL')),
]
