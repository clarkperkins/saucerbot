# -*- coding: utf-8 -*-

from saucerbot import db, Model


class User(Model):
    id = db.Column(db.Integer, primary_key=True)
    groupme_id = db.Column(db.String(15), unique=True)
    saucer_id = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.groupme_id)


class RemindPost(Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    group_id = db.Column(db.String(30))
    message_id = db.Column(db.String(30), unique=True)

    @classmethod
    def from_message(cls, message):
        return cls(
            date=message.created_at.date(),
            group_id=message.group_id,
            message_id=message.id,
        )
