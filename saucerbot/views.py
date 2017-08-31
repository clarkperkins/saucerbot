# -*- coding: utf-8 -*-

import logging

from flask import request
from flask.json import jsonify

from saucerbot import app

logger = logging.getLogger(__name__)


@app.route('/hooks/groupme/', methods=['POST'])
def groupme():
    message = request.get_json(force=True)

    logger.debug(message)

    if message['sender_type'] != 'user':
        return jsonify({})

    # Call all our handlers
    for handler in app.handlers:
        handler(message)

    response = {
        'ok': True
    }

    return jsonify(response)
