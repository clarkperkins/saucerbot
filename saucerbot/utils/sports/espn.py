# -*- coding: utf-8 -*-
import datetime

from pydantic import BaseModel


class ESPNSeason(BaseModel):
    type: int
    year: int


class ESPNWeek(BaseModel):
    number: int


class ESPNTeam(BaseModel):
    id: int
    uid: str
    location: str
    name: str
    abbreviation: str
    displayName: str
    shortDisplayName: str
    isActive: bool


class ESPNEventStatus(BaseModel):
    class Type(BaseModel):
        completed: bool

    clock: float
    displayClock: str
    period: int
    type: Type


class ESPNFootballEvent(BaseModel):
    class Competition(BaseModel):
        class Competitor(BaseModel):
            id: int
            uid: str
            type: str
            homeAway: str
            winner: bool | None = None
            team: ESPNTeam
            score: int

        id: int
        uid: str
        date: datetime.datetime
        competitors: list[Competitor]
        status: ESPNEventStatus

    id: int
    uid: str
    date: datetime.datetime
    name: str
    shortName: str
    season: ESPNSeason
    week: ESPNWeek
    competitions: list[Competition]
    status: ESPNEventStatus


class ESPNScoreboard(BaseModel):
    events: list[ESPNFootballEvent]
