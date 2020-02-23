#!/bin/bash

set -e

export SCOUT_MONITOR=true
export DJANGO_ENV=build
export HEROKU_APP_NAME=build

# Precompile the sources
python -m compileall saucerbot

# Generate static files
python manage.py collectstatic --noinput

# collectstatic ends up installing the scout agent, so remove the tarball
rm -f $SCOUT_CORE_AGENT_DIR/scout_apm_core-*-*/scout_apm_core-*-*.tgz
