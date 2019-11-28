FROM python:3.8-alpine

LABEL org.opencontainers.image.title="saucerbot"
LABEL org.opencontainers.image.description="GroupMe bot for the saucer groupme"
LABEL org.opencontainers.image.source="https://github.com/clarkperkins/saucerbot"

# These don't get removed, so install them first separately
RUN apk add --no-cache curl postgresql-client postgresql-libs

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off

# required for the scout agent to work
ENV SCOUT_CORE_AGENT_TRIPLE x86_64-unknown-linux-musl
ENV SCOUT_CORE_AGENT_DIR /app/scout_apm_core

# Passing the -h /app will set that as the home dir & chown it
RUN addgroup -S saucerbot && adduser -D -S -g saucerbot -G saucerbot -h /app saucerbot

WORKDIR /app

COPY --chown=saucerbot:saucerbot Pipfile Pipfile.lock manage.py /app/

# Install all the deps & uninstall build-time reqs all in one step to reduce image size
RUN apk add --no-cache --virtual .build-deps git gcc g++ linux-headers postgresql-dev && \
    pip install pipenv && \
    pipenv install --deploy --system && \
    pip uninstall -y pipenv virtualenv virtualenv-clone && \
    apk --purge del .build-deps

USER saucerbot

# pre-install the scout agent
RUN SCOUT_MONITOR=true python -c 'from scout_apm.core import install; install()' && \
    rm -f $SCOUT_CORE_AGENT_DIR/scout_apm_core-*-$SCOUT_CORE_AGENT_TRIPLE/scout_apm_core-*-$SCOUT_CORE_AGENT_TRIPLE.tgz

# Copy all the code & generate the static files
COPY --chown=saucerbot:saucerbot saucerbot saucerbot

RUN python -m compileall saucerbot

# Build static files
RUN DJANGO_ENV=build HEROKU_APP_NAME=build python manage.py collectstatic --noinput

# Put these args here so that changing them doesn't invalidate the build cache
ARG BUILD_DATE=""
ARG GIT_COMMIT=""

LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.revision="$GIT_COMMIT"

ENV GIT_COMMIT=$GIT_COMMIT

CMD ["gunicorn", "saucerbot.wsgi"]

HEALTHCHECK --timeout=5s CMD curl -f http://localhost:$PORT/groupme/login/ || exit 1
