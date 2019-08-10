#!/bin/bash

docker tag clarkperkins/elastic-apm-server registry.heroku.com/saucerbot-apm/web
docker push registry.heroku.com/saucerbot-apm/web

heroku container:release -a saucerbot-apm web
