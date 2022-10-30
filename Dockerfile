FROM python:3.10-slim AS build

WORKDIR /app

COPY docker/install_build.sh /app/
RUN sh install_build.sh

COPY pyproject.toml poetry.lock manage.py logging.yaml gunicorn.conf.py /app/

COPY saucerbot saucerbot

# Install poetry
RUN python -m pip install poetry virtualenv

ENV VIRTUAL_ENV /app/venv

# Create & activate virtualenv
RUN virtualenv $VIRTUAL_ENV
ENV PATH $VIRTUAL_ENV/bin:$PATH

# Install python dependencies
RUN poetry install --sync --without=dev

# Precompile the sources
RUN python -m compileall saucerbot

# Need these for collectstatic to work
ENV DJANGO_ENV build

# Generate static files
RUN python manage.py collectstatic --noinput


FROM python:3.10-slim AS saucerbot

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off

# Passing the -d /app will set that as the home dir & chown it
RUN useradd -r -U -m -d /app saucerbot

WORKDIR /app

COPY --chown=saucerbot:saucerbot docker/install_runtime.sh /app/
RUN sh install_runtime.sh

COPY --chown=saucerbot:saucerbot --from=build /app /app

ENV VIRTUAL_ENV /app/venv
ENV PATH $VIRTUAL_ENV/bin:$PATH

USER saucerbot
