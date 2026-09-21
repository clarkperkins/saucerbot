# -*- coding: utf-8 -*-

import os

# Django 6 deprecated the EMAIL_* settings in favor of MAILERS (they go away
# in 7.0) and raises ImproperlyConfigured if both are defined. OPTIONS are
# passed straight through to the backend's constructor.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.sendgrid.net",
            "port": 587,
            "username": "apikey",
            "password": os.environ.get("SENDGRID_API_KEY"),
            "use_tls": True,
        },
    },
}

EMAIL_SUBJECT_PREFIX = "[saucerbot] "

SERVER_EMAIL = "noreply@clarkperkins.com"

# Django 6 replaced the (name, address) pairs here with plain address strings.
# The entry is still dropped when ADMIN_EMAIL is unset: otherwise the address
# list is [None] and mail_admins() raises ImproperlyConfigured from inside the
# 500 handler.
_admin_email = os.environ.get("ADMIN_EMAIL")

ADMINS = [f"Saucerbot Admin <{_admin_email}>"] if _admin_email else []
