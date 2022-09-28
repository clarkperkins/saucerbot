#!/bin/bash

set -e

export BUILD_PACKAGES='curl gcc g++ git gnupg'
export PG_BUILD_PACKAGES='libpq-dev'

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends $BUILD_PACKAGES

echo "Installing postgresql-client..."
. /etc/os-release
echo "deb http://apt.postgresql.org/pub/repos/apt/ ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/pgdg.list
curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y --no-install-recommends $PG_BUILD_PACKAGES
