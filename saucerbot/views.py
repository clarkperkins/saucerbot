# -*- coding: utf-8 -*-

import json
import logging

from flask import request
from flask.json import jsonify

from saucerbot import app

logger = logging.getLogger(__name__)


@app.route('/hooks/groupme/', methods=['POST'])
def groupme():
    message = request.get_json(force=True)

    logger.info('Received message: {}'.format(json.dumps(message)))

    if message['sender_type'] == 'bot' and message['name'] == 'saucerbot':
        return jsonify({})

    # Call all our handlers
    for handler in app.handlers:
        logger.debug('Trying message handler {} ...'.format(handler.__name__))
        handler(message)

    response = {
        'ok': True
    }

    return jsonify(response)
