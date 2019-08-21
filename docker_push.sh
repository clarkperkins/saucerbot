#!/bin/bash

docker login -u "$HEROKU_USERNAME" -p "$HEROKU_API_KEY" registry.heroku.com

if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
    APP_NAME="saucerbot-staging-pr-$TRAVIS_PULL_REQUEST"
    TAG_NAME="registry.heroku.com/$APP_NAME/web"
    echo "PR detected - deploying to $TAG_NAME"
    docker tag clarkperkins/saucerbot $TAG_NAME
    docker push $TAG_NAME
    heroku container:release -a $APP_NAME
elif [ "$TRAVIS_BRANCH" == "master" ]; then
    APP_NAME="saucerbot-staging"
    TAG_NAME="registry.heroku.com/$APP_NAME/web"
    echo "master branch detected - deploying to $TAG_NAME"
    docker tag clarkperkins/saucerbot $TAG_NAME
    docker push $TAG_NAME
    heroku container:release -a $APP_NAME

    echo "Pushing to docker hub"
    docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
    docker push clarkperkins/saucerbot
else
    echo "Not deploying image"
fi
