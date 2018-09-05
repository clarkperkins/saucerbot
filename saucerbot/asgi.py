# -*- coding: utf-8 -*-
"""
ASGI config for saucerbot project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://github.com/django/asgiref
"""

import os

import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saucerbot.settings")
os.environ.setdefault("DJANGO_ENV", "production")

# Django must be setup before getting the application
django.setup()

application = get_default_application()
