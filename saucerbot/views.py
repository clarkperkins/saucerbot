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

    logger.info('Received raw message: {}'.format(json.dumps(message)))

    # Load it as a groupme message
    message = app.group.bot_message(message)

    # We don't want to accidentally respond to ourself
    if message.sender_type == 'bot' and message.name == 'saucerbot':
        return jsonify({'message_sent': False})

    message_sent = False

    # Call all our handlers
    for handler in app.handlers:
        logger.debug('Trying message handler {} ...'.format(handler.func.__name__))

        if handler.regex:
            # This is a regex handler, special case
            match = handler.regex.search(message.text)
            if match:
                # We matched!  Now call our handler and break out of the loop
                handler.func(message, match)
                message_sent = True
                break
        else:
            # Just a plain handler.
            # If it returns something truthy, it matched, so it means we should stop
            if handler.func(message):
                message_sent = True
                break

    response = {
        'message_sent': message_sent,
    }

    return jsonify(response)
