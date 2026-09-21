# -*- coding: utf-8 -*-

import os

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = "[saucerbot] "

SERVER_EMAIL = "noreply@clarkperkins.com"

# ADMIN_EMAIL is read from the environment, and when it is unset the entry
# becomes ("Saucerbot Admin", None), which mail_admins() turns into a
# recipient list of [None]: it sends nothing and says nothing. Django 6 turns
# the same config into an ImproperlyConfigured raised from inside the 500
# handler. Drop the entry entirely so mail_admins() returns on purpose.
_admin_email = os.environ.get("ADMIN_EMAIL")

ADMINS = [("Saucerbot Admin", _admin_email)] if _admin_email else []
