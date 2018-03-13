# -*- coding: utf-8 -*-

import inspect
import json
import logging

from flask import request
from flask.json import jsonify
from lowerpines.endpoints.message import Message

from saucerbot import app, the_dores

logger = logging.getLogger(__name__)


@app.route('/hooks/groupme/', methods=['POST'])
def groupme():
    message = request.get_json(force=True)

    logger.info('Received raw message: {}'.format(json.dumps(message)))

    # Load it as a groupme message
    message: Message = Message.from_json(app.gmi, message)

    # We don't want to accidentally respond to ourself
    if message.sender_type == 'bot' and 'saucerbot' in message.name:
        return jsonify({'message_sent': False})

    message_sent = False

    # Call all our handlers
    for handler in app.handlers:
        logger.debug(f"Trying message handler {handler.func.__name__} ...")

        if handler.regex:
            # This is a regex handler, special case
            match = handler.regex.search(message.text)
            if match:
                # We matched!  Now call our handler and break out of the loop

                # We want to see what arguments our function takes, though.
                sig = inspect.signature(handler.func)

                kwargs = {}
                if 'message' in sig.parameters:
                    kwargs['message'] = message
                if 'match' in sig.parameters:
                    kwargs['match'] = match

                handler.func(**kwargs)
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


@app.route('/hooks/dores-win', methods=['POST'])
def did_the_dores_win():
    logger.info("Request to /hooks/dores-win")
    result = the_dores.did_the_dores_win(False, False)
    if result:
        app.bot.post(result)
    response = {
        'ok': True,
        'win': result is not None,
        'result': result
    }
    return jsonify(response)
