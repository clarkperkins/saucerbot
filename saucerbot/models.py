# -*- coding: utf-8 -*-


from sqlalchemy import Column, Integer, String

from saucerbot.database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    saucer_id = Column(String(10), unique=True)

    def __init__(self, name=None, saucer_id=None):
        self.name = name
        self.saucer_id = saucer_id

    def __repr__(self):
        return '<User {}>'.format(self.name)
