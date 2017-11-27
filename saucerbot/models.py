# -*- coding: utf-8 -*-

from saucerbot import db, Model


class User(Model):
    id = db.Column(db.Integer, primary_key=True)
    groupme_id = db.Column(db.String(15), unique=True)
    saucer_id = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.groupme_id)
