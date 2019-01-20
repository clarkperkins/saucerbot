# -*- coding: utf-8 -*-

import os

from django.core.exceptions import ImproperlyConfigured
from split_settings.tools import include

# Managing environment via DJANGO_ENV variable:
ENV = os.environ.get('DJANGO_ENV')

if not ENV:
    raise ImproperlyConfigured('You must define the environment variable DJANGO_ENV.')

# Include settings:
include(
    'base.py',
    'email.py',
    'logging.py',

    # Select the right env:
    f'environments/{ENV}.py',
)
