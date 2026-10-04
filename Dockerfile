FROM python:3.14-slim AS build

WORKDIR /app

COPY docker/install_build.sh /app/
RUN sh install_build.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
# renovate: datasource=pypi depName=uv
ARG UV_VERSION=0.12.23
RUN python -m pip install --no-cache-dir uv==${UV_VERSION}

# Build the virtualenv where the runtime stage expects it, against the image's
# own interpreter rather than a uv-managed download.
ENV VIRTUAL_ENV=/app/venv
ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_LINK_MODE=copy
ENV PATH=$VIRTUAL_ENV/bin:$PATH

# Install python dependencies (but not self)
COPY pyproject.toml uv.lock manage.py logging.yaml gunicorn.conf.py README.rst /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Copy self & install
COPY saucerbot saucerbot
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Need these for collectstatic to work
ENV DJANGO_ENV=build

# Generate static files
RUN python manage.py collectstatic --noinput


FROM python:3.14-slim AS saucerbot

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off

# Passing the -d /app will set that as the home dir & chown it
RUN useradd -r -U -m -d /app saucerbot

WORKDIR /app

COPY --chown=saucerbot:saucerbot docker/install_runtime.sh /app/
RUN sh install_runtime.sh

COPY --chown=saucerbot:saucerbot --from=build /app /app

ENV VIRTUAL_ENV=/app/venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH

USER saucerbot
