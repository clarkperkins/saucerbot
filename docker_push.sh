#!/bin/bash

docker login -u "$HEROKU_USERNAME" -p "$HEROKU_API_KEY" registry.heroku.com

if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
    TAG_NAME="registry.heroku.com/saucerbot-staging-pr-$TRAVIS_PULL_REQUEST/web"
    echo "PR detected - deploying to $TAG_NAME"
    docker tag clarkperkins/saucerbot $TAG_NAME
    docker push $TAG_NAME
elif [ "$TRAVIS_BRANCH" == "master" ]; then
    TAG_NAME="registry.heroku.com/saucerbot-staging/web"
    echo "master branch detected - deploying to $TAG_NAME"
    docker tag clarkperkins/saucerbot $TAG_NAME
    docker push $TAG_NAME

    echo "Pushing to docker hub"
    docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
    docker push clarkperkins/saucerbot
else
    echo "Not deploying image"
fi
