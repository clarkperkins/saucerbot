#!/bin/bash

docker pull registry.heroku.com/saucerbot-staging/web
docker tag registry.heroku.com/saucerbot-staging/web registry.heroku.com/saucerbot/web
docker push registry.heroku.com/saucerbot/web

heroku container:release -a saucerbot web
