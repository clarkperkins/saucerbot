#!/bin/bash

if [ ! -z "$TRAVIS_PULL_REQUEST_BRANCH" ]; then
  git_branch=$TRAVIS_PULL_REQUEST_BRANCH
  git_status=""
elif [ ! -z "$TRAVIS_BRANCH" ]; then
  git_branch=$TRAVIS_BRANCH
  git_status=""
else
  git_branch=$(git branch --show-current)
  git_status=$(git status --porcelain)
fi

echo "Located git branch: $git_branch"
echo "With git status:"
echo $git_status

make build

docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"

if [ "$git_branch" == "main" ] && [ -z "$git_status" ]; then
    echo "Pushing docker image clarkperkins/saucerbot"
    docker push clarkperkins/saucerbot
fi

image="clarkperkins/saucerbot:$(echo $git_branch | tr '/' '-')"

echo "Pushing docker image $image"

docker tag clarkperkins/saucerbot $image
docker push $image
