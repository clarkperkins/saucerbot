#!/bin/bash

if [ "$TRAVIS_BRANCH" == "master" ] && [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    bake build

    echo "Pushing to docker hub"
    docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
    docker push clarkperkins/saucerbot
else
    echo "Not deploying image"
fi
