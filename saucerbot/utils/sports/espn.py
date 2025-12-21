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
    location: str
    displayName: str

    # Unused below
    # id: int
    # uid: str
    # abbreviation: str
    # name: str
    # shortDisplayName: str
    # color: str
    # alternativeColor: str
    # isActive: bool
    # venue: ESPNVenue
    # links: list[ESPNLink]
    # logo: str
    # conferenceId: int


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

    type: Type

    # Unused below
    # clock: float
    # displayClock: str
    # period: int


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

            score: int
            team: ESPNTeam

            # Unused below
            # id: int
            # uid: str
            # order: int
            # homeAway: str
            # winner: bool | None = None
            # linescores: list[ESPNLineScore] | None = None
            # statistics: list | None = None
            # curatedRank: ESPNCuratedRank | None = None
            # records: list[Record] | None = None
            # Apparently using `# type: xxx` is another means of type-checking recognized by mypy, so double-commenting
            # # type: str

        class Groups(BaseModel):
            id: int
            name: str
            shortName: str
            isConference: bool

        competitors: list[Competitor]

        # Unused below
        # id: int
        # uid: str
        # date: datetime.datetime
        # attendance: int
        # timeValid: bool
        # dateValid: bool
        # neutralSite: bool
        # conferenceCompetition: bool
        # recent: bool
        # venue: dict
        # notes: list[dict]
        # status: ESPNEventStatus
        # broadcasts: list[ESPNBroadcast]
        # leaders: list[dict] | None = None
        # groups: Groups | None = None
        # format: dict
        # startDate: datetime.datetime
        # broadcast: str
        # geoBroadcasts: list[dict]
        # highlights: list[dict]
        # headlines: list[dict] | None = None
        # Apparently using `# type: xxx` is another means of type-checking recognized by mypy, so double-commenting
        # # type: Type

    date: datetime.datetime
    status: ESPNEventStatus
    competitions: list[Competition]

    # Unused below
    # id: int
    # uid: str
    # name: str
    # shortName: str
    # season: ESPNSeason
    # week: ESPNWeek
    # links: list[ESPNLink]


class ESPNScoreboard(BaseModel):
    events: list[ESPNFootballEvent]

    # Unused Below
    # leagues: list[dict]
    # groups: list[int]
    # season: ESPNSeason
    # week: ESPNWeek
