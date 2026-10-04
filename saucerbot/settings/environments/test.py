# -*- coding: utf-8 -*-

SECRET_KEY = "abcdef123456"

DEBUG = True

ALLOWED_HOSTS = ["*"]

SERVER_DOMAIN = "localhost"

# No DATABASES override here on purpose. base.py leaves it empty when
# DATABASE_URL is unset, and tests/conftest.py fills it in from the PostgreSQL
# container it starts -- unconditionally, so DATABASE_URL does not reach a test
# run either way. There is no fallback engine: anything reaching for a database
# outside that fixture fails loudly rather than quietly running on something
# production does not use.
