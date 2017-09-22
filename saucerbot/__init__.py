# -*- coding: utf-8 -*-

import logging.config
import os
import typing

import yaml
from flask_sqlalchemy import SQLAlchemy, Model as FlaskModel

from saucerbot.flask import SaucerFlask

APP_HOME = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Configure logging
with open(os.path.join(APP_HOME, 'config', 'logging.yaml')) as f:
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
import saucerbot.commands
import saucerbot.handlers
import saucerbot.views
