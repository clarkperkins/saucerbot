# -*- coding: utf-8 -*-

import datetime

import click

from saucerbot import app, utils


@app.cli.command()
def initdb():
    """
    Initializes the database.
    """
    from saucerbot.database import init_db

    init_db()
    click.echo('Initialized the database.')


@app.cli.command()
@click.option('--force', is_flag=True, help='Forces saucerbot to send a reminder on non-mondays')
def remind(force):
    """
    Remind everyone to come to saucer
    """
    today = datetime.datetime.now()

    if today.weekday() == 0 or force:
        utils.send_message('Saucer at 7PM. Like if.')
    else:
        click.echo("Not sending message, it's not Monday!")


@app.cli.command('load-beers')
def load_beers():
    """
    Load all the beers
    """
    utils.load_beers_into_es()
