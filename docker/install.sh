#!/bin/bash

set -e

export PACKAGES='curl postgresql-client-11'
export BUILD_PACKAGES='gcc g++'

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends $PACKAGES $BUILD_PACKAGES

echo "Installing pipenv..."
pip install pipenv

echo "Installing python dependencies..."
pipenv install --deploy --system

echo "Removing pipenv..."
pip uninstall -y appdirs distlib filelock pipenv virtualenv virtualenv-clone

echo "Removing unneeded system dependencies..."
apt-get remove -y $BUILD_PACKAGES
apt-get -y autoremove
rm -rf /var/lib/apt/lists/*
