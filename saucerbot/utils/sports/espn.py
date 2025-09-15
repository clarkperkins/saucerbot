# -*- coding: utf-8 -*-
import datetime

from pydantic import BaseModel


class ESPNSeason(BaseModel):
    type: int
    year: int


class ESPNWeek(BaseModel):
    number: int


class ESPNVenue(BaseModel):
    id: int


class ESPNLink(BaseModel):
    rel: list[str]
    href: str
    text: str
    isExternal: bool
    isPremium: bool


class ESPNTeam(BaseModel):
    id: int
    uid: str
    location: str
    name: str
    abbreviation: str
    displayName: str
    shortDisplayName: str
    color: str
    alternativeColor: str | None = None
    isActive: bool
    venue: ESPNVenue
    links: list[ESPNLink]
    logo: str
    conferenceId: int


class ESPNLineScore(BaseModel):
    displayValue: str
    period: int
    value: float


class ESPNCuratedRank(BaseModel):
    current: int


class ESPNBroadcast(BaseModel):
    market: str
    names: list[str]


class ESPNEventStatus(BaseModel):
    class Type(BaseModel):
        completed: bool

    clock: float
    displayClock: str
    period: int
    type: Type


class ESPNFootballEvent(BaseModel):
    class Competition(BaseModel):
        class Type(BaseModel):
            abbreviation: str
            id: int

        class Competitor(BaseModel):
            class Record(BaseModel):
                name: str
                summary: str
                type: str
                abbreviation: str | None = None

            id: int
            uid: str
            type: str
            order: int
            homeAway: str
            winner: bool
            team: ESPNTeam
            score: int
            linescores: list[ESPNLineScore]
            statistics: list
            curatedRank: ESPNCuratedRank
            records: list[Record]

        class Groups(BaseModel):
            id: int
            name: str
            shortName: str
            isConference: bool

        id: int
        uid: str
        date: datetime.datetime
        attendance: int
        type: Type
        timeValid: bool
        dateValid: bool
        neutralSite: bool
        conferenceCompetition: bool
        recent: bool
        venue: dict
        competitors: list[Competitor]
        notes: list[str]
        status: ESPNEventStatus
        broadcasts: list[ESPNBroadcast]
        leaders: list[dict]
        groups: Groups | None = None
        format: dict
        startDate: datetime.datetime
        broadcast: str
        geoBroadcasts: list[dict]
        highlights: list[dict]
        headlines: list[dict] | None = None

    id: int
    uid: str
    date: datetime.datetime
    name: str
    shortName: str
    season: ESPNSeason
    week: ESPNWeek
    competitions: list[Competition]
    links: list[ESPNLink]
    status: ESPNEventStatus


class ESPNScoreboard(BaseModel):
    leagues: list[dict]
    groups: list[int]
    season: ESPNSeason
    week: ESPNWeek
    events: list[ESPNFootballEvent]
