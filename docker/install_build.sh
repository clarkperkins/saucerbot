#!/bin/bash

set -e

export BUILD_PACKAGES='ca-certificates curl gcc g++ git gnupg'
export PG_BUILD_PACKAGES='libpq-dev'

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends $BUILD_PACKAGES

echo "Installing postgresql-client..."
install -d /usr/share/postgresql-common/pgdg
curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc

. /etc/os-release
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/pgdg.list

apt-get update
apt-get install -y --no-install-recommends $PG_BUILD_PACKAGES
