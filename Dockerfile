FROM dhi.io/python:3.13-dev AS build

WORKDIR /app

COPY docker/install_build.sh /app/
RUN sh install_build.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install poetry
RUN python -m pip install poetry virtualenv

ENV VIRTUAL_ENV=/app/venv

# Create & activate virtualenv
RUN virtualenv $VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# Install python dependencies (but not self)
COPY pyproject.toml poetry.lock manage.py logging.yaml gunicorn.conf.py README.rst /app/
RUN poetry sync --without=dev --no-root

# Copy self, set the version & install
COPY saucerbot saucerbot
RUN poetry version $(date +"%Y.%m.%d")
RUN poetry sync --without=dev

# Need these for collectstatic to work
ENV DJANGO_ENV=build

# Generate static files
RUN python manage.py collectstatic --noinput


FROM dhi.io/python:3.13-dev AS saucerbot

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off

WORKDIR /app

COPY --chown=nonroot:nonroot docker/install_runtime.sh /app/
RUN sh install_runtime.sh

USER nonroot

COPY --chown=nonroot:nonroot --from=build /app /app

ENV VIRTUAL_ENV=/app/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH
