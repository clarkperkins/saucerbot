# -*- coding: utf-8 -*-

import random
import re
from typing import Any, Dict, List

import arrow
from arrow.parser import ParserError

from saucerbot.parsers import BridgestoneEventsParser

__bridgestone_time_pattern = 'MMM. D - h:mm A'
__message_formats = [
    "Better get there early: {event} at Bridgestone at {time} tonight!",
    "Just so you know, {event} at Bridgestone tonight at {time}.",
    "Parking might be rough tonight: {event} at Bridgestone at {time}",
    "WARNING! At {time}, {event} at Bridgestone tonight!"
]
__preds_quips = [
    "the Perds take on the {team}",
    "the {team} come to town to play the Preds",
    "your Nashville Predators are kicking some {team} butt"
]

__general_quips = [
    "Nashvillians are coming in to catch {name}",
    "{name} will be",
    "people from all over are coming to see {name}"
]


def get_todays_events() -> List[Dict[str, Any]]:
    today = arrow.now('US/Central')
    events = []
    for ev in BridgestoneEventsParser().parse():
        try:
            event_date = arrow.get(ev['date'], __bridgestone_time_pattern)
        except ParserError:
            # Date won't parse, just skip it
            continue
        if today.day == event_date.day \
                and today.month == event_date.month \
                and event_date.hour >= 12:
            events.append(ev)
    return events


def create_message(event: Dict[str, Any]) -> str:
    template = random.choice(__message_formats)
    time_string = arrow.get(event['date'], __bridgestone_time_pattern).format('h:mm')
    preds_match = re.fullmatch('Nashville Predators vs. ([A-Za-z. ]+)', event['name'])
    if preds_match:
        team = preds_match.group(1)
        event_string = random.choice(__preds_quips).format(team=team)
    else:
        event_string = random.choice(__general_quips).format(name=event['name'])
    return template.format(event=event_string, time=time_string)
