# -*- coding: utf-8 -*-

import logging.config
import os

import yaml

from saucerbot.app import SaucerFlask


APP_HOME = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Configure logging
with open(os.path.join(APP_HOME, 'config', 'logging.yaml')) as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger(__name__)

# Create our app
app = SaucerFlask(__name__)


# So our views get loaded AFTER the app gets created
import saucerbot.commands
import saucerbot.handlers
import saucerbot.views

from saucerbot.database import session


# Add the teardown for the database
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()
