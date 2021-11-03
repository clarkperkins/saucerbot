#!/bin/bash

set -e

export PACKAGES='curl'
export BUILD_PACKAGES='gcc g++ git gnupg'
export PG_PACKAGES='postgresql-client-14'
export PG_BUILD_PACKAGES='libpq-dev'

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends $PACKAGES $BUILD_PACKAGES

echo "Installing postgresql-client..."
. /etc/os-release
echo "deb http://apt.postgresql.org/pub/repos/apt/ ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y --no-install-recommends $PG_PACKAGES $PG_BUILD_PACKAGES

echo "Installing pipenv..."
python -m pip install pipenv

echo "Installing python dependencies..."
pipenv install --deploy --system

echo "Removing pipenv..."
python -m pip uninstall -y backports.entry-points-selectable distlib filelock pipenv platformdirs virtualenv virtualenv-clone

echo "Removing unneeded system dependencies..."
apt-get remove -y $BUILD_PACKAGES $PG_BUILD_PACKAGES
apt-get -y autoremove
rm -rf /var/lib/apt/lists/*
