# -*- coding: utf-8 -*-

import os

import dj_database_url

os.environ.setdefault(
    "DATABASE_URL", "postgres://postgres:postgres@localhost:5432/postgres"
)
os.environ.setdefault("BONSAI_URL", "http://localhost:9200")

SECRET_KEY = "abcdef123456"

DEBUG = True

SERVER_DOMAIN = "localhost"

ALLOWED_HOSTS = ["*"]

# Don't require SSL for dev
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600),
}
