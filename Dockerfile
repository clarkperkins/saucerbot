FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off

# required for the scout agent to work
ENV SCOUT_CORE_AGENT_DIR /app/scout_apm_core

# Passing the -d /app will set that as the home dir & chown it
RUN useradd -r -U -m -d /app saucerbot

WORKDIR /app

COPY --chown=saucerbot:saucerbot Pipfile Pipfile.lock manage.py logging.yaml gunicorn.conf.py docker/install.sh docker/build.sh /app/

# Install all the deps & uninstall build-time reqs all in one step to reduce image size
RUN sh install.sh

USER saucerbot

# Copy all the code & generate the static files
COPY --chown=saucerbot:saucerbot saucerbot saucerbot

# run the final build steps
RUN sh build.sh

CMD ["gunicorn", "saucerbot.wsgi"]

HEALTHCHECK --timeout=5s CMD curl -f http://localhost:$PORT || exit 1
