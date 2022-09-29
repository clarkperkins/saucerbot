#!/bin/bash

set -e

export PACKAGES='curl gnupg'
export PG_PACKAGES='postgresql-client-14'

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends $PACKAGES

echo "Installing postgresql-client..."
. /etc/os-release
echo "deb http://apt.postgresql.org/pub/repos/apt/ ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y --no-install-recommends $PG_PACKAGES

echo "Cleaning up apt-get..."
apt-get -y autoremove
apt-get clean
rm -rf /var/lib/apt/lists/*
