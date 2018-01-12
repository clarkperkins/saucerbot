# -*- coding: utf-8 -*-

import io
import logging.config
import os

import yaml
from flask_sqlalchemy import SQLAlchemy, Model as FlaskModel

from saucerbot.flask import SaucerFlask

APP_HOME = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Configure logging
with io.open(os.path.join(APP_HOME, 'config', 'logging.yaml'), 'rt') as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger: logging.Logger = logging.getLogger(__name__)

# Create our app
app = SaucerFlask('saucerbot')

# Create the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Model: FlaskModel = db.Model

# So our views get loaded AFTER the app gets created
import saucerbot.commands  # noqa
import saucerbot.handlers  # noqa
import saucerbot.views  # noqa
