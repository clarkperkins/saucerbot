# -*- coding: utf-8 -*-

from saucerbot.settings.base import MIDDLEWARE

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'BUILD_FAKE_SECRET_KEY'

# Configure whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
