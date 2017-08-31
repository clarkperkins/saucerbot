# -*- coding: utf-8 -*-

from saucerbot import app
from saucerbot.utils import send_message


@app.cli.command()
def remind():
    """
    Remind everyone to come to saucer
    """
    send_message('Saucer at 7PM. Like if.')
