FROM python:3.8-slim

LABEL org.opencontainers.image.title="saucerbot"
LABEL org.opencontainers.image.description="GroupMe bot for the saucer groupme"
LABEL org.opencontainers.image.source="https://github.com/clarkperkins/saucerbot"

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off

# required for the scout agent to work
ENV SCOUT_CORE_AGENT_DIR /app/scout_apm_core

# Passing the -h /app will set that as the home dir & chown it
RUN useradd -r -U -m -d /app saucerbot

WORKDIR /app

COPY --chown=saucerbot:saucerbot Pipfile Pipfile.lock manage.py docker/install.sh /app/

# Install all the deps & uninstall build-time reqs all in one step to reduce image size
RUN sh install.sh

USER saucerbot

# Copy all the code & generate the static files
COPY --chown=saucerbot:saucerbot saucerbot saucerbot
COPY --chown=saucerbot:saucerbot docker/build.sh .

# run the final build steps
RUN sh build.sh

# Put these args here so that changing them doesn't invalidate the build cache
ARG BUILD_DATE=""
ARG GIT_COMMIT=""

LABEL org.opencontainers.image.created="$BUILD_DATE"
LABEL org.opencontainers.image.revision="$GIT_COMMIT"

ENV GIT_COMMIT=$GIT_COMMIT

CMD ["gunicorn", "saucerbot.wsgi"]

HEALTHCHECK --timeout=5s CMD curl -f http://localhost:$PORT/groupme/login/ || exit 1
