# -*- coding: utf-8 -*-

import datetime

import click

from saucerbot import app
from saucerbot.utils import send_message
from saucerbot.bridgestone import get_todays_events
from saucerbot.bridgestone import create_message


@app.cli.command()
@click.option('--force', is_flag=True, help='Forces saucerbot to send a reminder on non-mondays')
def remind(force):
    """
    Remind everyone to come to saucer
    """
    today = datetime.datetime.now()

    if today.weekday() == 0 or force:
        send_message('Saucer at 7PM. Like if.')
        todays_events = get_todays_events()
        if len(todays_events) > 0:
            send_message(create_message(todays_events[0]))
    else:
        click.echo("Not sending message, it's not Monday!")
