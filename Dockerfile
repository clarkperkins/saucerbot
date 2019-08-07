ARG INSTALL_TYPE

# Base image. Installs base libs required for runtime, creates users/dirs, etc
FROM python:3.7-alpine AS base

# These don't get removed, so install them first separately
RUN apk add --no-cache curl 'postgresql-libs=~11.4'

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off

# Passing the -h /app will set that as the home dir & chown it
RUN addgroup -S saucerbot && adduser -D -S -g saucerbot -G saucerbot -h /app saucerbot

WORKDIR /app
# END base image



# Fast installation - install pre-built alpine wheels from fury.
# Expect fresh install with no caches to take ~25s.
FROM base AS fast

# Using requirements.txt instead of pipenv so we can override the index url more easily.
COPY --chown=saucerbot:saucerbot requirements.txt manage.py /app/

RUN pip install -r requirements.txt --index-url https://pypi.fury.io/clarkperkins --extra-index-url https://pypi.org/simple
# END fast install



# Full installation - compile all of the python deps at build time
# Expect fresh install with no caches to take ~65s.
FROM base AS full

COPY --chown=saucerbot:saucerbot Pipfile Pipfile.lock manage.py /app/

# Install all the deps & uninstall build-time reqs all in one step to reduce image size
RUN apk add --no-cache --virtual .build-deps gcc g++ linux-headers postgresql-dev && \
    pip install pipenv && \
    pipenv install --deploy --system && \
    pip uninstall -y pipenv virtualenv virtualenv-clone && \
    apk --purge del .build-deps
# END full install


# Copy all the code & generate the static files. Must start from either the fast or full install.
FROM $INSTALL_TYPE

COPY --chown=saucerbot:saucerbot saucerbot saucerbot

USER saucerbot

# Get the scout core agent working properly
ENV SCOUT_CORE_AGENT_TRIPLE x86_64-unknown-linux-musl
ENV SCOUT_CORE_AGENT_DIR /app/scout_apm_core
RUN SCOUT_MONITOR=true python -c 'from scout_apm.core import install; install()'

# Build static files
RUN DJANGO_ENV=build python manage.py collectstatic --noinput

CMD ["gunicorn", "saucerbot.wsgi"]
