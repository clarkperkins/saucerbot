# -*- coding: utf-8 -*-
"""
Django settings for the saucerbot project.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Pull a few things from the heroku environment
HEROKU_APP_NAME: str | None = os.environ.get("HEROKU_APP_NAME")
DISCORD_APPLICATION_ID: str | None = os.environ.get("DISCORD_APPLICATION_ID")
DISCORD_BOT_TOKEN: str | None = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CLIENT_ID: str | None = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET: str | None = os.environ.get("DISCORD_CLIENT_SECRET")
GROUPME_CLIENT_ID: str | None = os.environ.get("GROUPME_CLIENT_ID")
FLICKR_API_KEY: str | None = os.environ.get("FLICKR_API_KEY")
HEROKU_APP_DOMAIN: str | None = (
    f"{HEROKU_APP_NAME}.herokuapp.com" if HEROKU_APP_NAME else None
)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# Application definition

INSTALLED_APPS = [
    "scout_apm.django",
    "saucerbot.core",
    "saucerbot.discord",
    "saucerbot.groupme",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "rollbar.contrib.django.middleware.RollbarNotifierMiddleware",
]

ROOT_URLCONF = "saucerbot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "saucerbot.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600, ssl_require=True),
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "US/Central"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

WHITENOISE_KEEP_ONLY_HASHED_FILES = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Add modules here that contain handlers.
# They will get loaded when the server starts up

HANDLER_MODULES = [
    "saucerbot.handlers.general",
    "saucerbot.handlers.saucer",
    "saucerbot.handlers.vandy",
    "saucerbot.groupme.handlers",
]


REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rollbar.contrib.django_rest_framework.post_exception_handler",
}

# Scout config
SCOUT_NAME = HEROKU_APP_NAME

# Rollbar config
ROLLBAR = {
    "access_token": os.environ.get("ROLLBAR_ACCESS_TOKEN"),
    "environment": os.environ.get("DJANGO_ENV"),
    "root": BASE_DIR,
}
