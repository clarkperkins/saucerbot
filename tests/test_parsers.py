from typing import Any

import arrow
from bs4 import BeautifulSoup

from saucerbot.utils.base import get_new_arrivals
from saucerbot.utils.bridgestone import bridgestone_events_url
from saucerbot.utils.bridgestone import (
    get_event_time_helper,
    get_all_events,
    get_events_for_date,
    get_event_time,
)
from saucerbot.utils.parsers import HtmlContentProvider, NewArrivalsParser


class LocalFileContentProvider(HtmlContentProvider):
    def __init__(self, file_path):
        super().__init__("")
        self.file_path = file_path

    def get_content(self) -> BeautifulSoup:
        with open(self.file_path, "r") as fp:
            content = "".join(fp.readlines())
            return BeautifulSoup(content, "html.parser")


def create_event(name: str, month: int, date: int) -> dict[str, Any]:
    return {"name": name, "parsed_date": arrow.get(2000, month, date)}


def event_equals(expected, actual) -> bool:
    if expected["name"] == actual["name"]:
        date0 = expected["parsed_date"]
        date1 = actual["parsed_date"]
        return date0.day == date1.day and date0.month == date1.month
    return False


expected_events = [
    create_event("Panthers vs. Predators", 4, 26),
    create_event("Panthers vs. Predators", 4, 27),
    create_event("Stars vs. Predators", 5, 1),
    create_event("Hurricanes vs. Predators", 5, 8),
    create_event("Hurricanes vs. Predators", 5, 10),
    create_event("CINCH World's Toughest Rodeo", 6, 12),
    create_event("ALABAMA with very special guest Martina McBride", 7, 3),
    create_event("RESCHEDULED: The Doobie Brothers", 7, 24),
    create_event("RESCHEDULED: Justin Bieber", 7, 26),
    create_event("RESCHEDULED: Luke Bryan", 7, 30),
    create_event("RESCHEDULED: Matchbox Twenty", 8, 4),
    create_event("RESCHEDULED: James Taylor", 8, 16),
]


def test_event_list_parsing():
    provider = LocalFileContentProvider("test_resources/events-sample.html")
    events_list = get_all_events(provider)

    assert len(expected_events) == len(events_list)
    for i in range(0, len(expected_events)):
        assert event_equals(expected_events[i], events_list[i])

    assert all([ev["details"] for ev in events_list])

    sample_date = arrow.get(2000, 8, 4)
    dated_events = get_events_for_date(events_list, sample_date)
    assert len(dated_events) == 1
    assert event_equals(expected_events[10], dated_events[0])


def test_event_time_parsing():
    provider = LocalFileContentProvider("test_resources/event-time-sample.html")
    event_name = "Panthers vs. Predators"  # Doesn't really matter
    extracted = get_event_time_helper(provider, event_name)

    assert extracted == "7:00"


def test_bridgestone_site_structure():
    """
    Tests to make sure the Bridgestone events site hasn't changed
    """
    all_events = get_all_events(HtmlContentProvider(bridgestone_events_url))
    assert len(all_events) > 0
    assert all([ev["name"] for ev in all_events])
    assert all([ev["details"] for ev in all_events])
    assert all([ev["parsed_date"] for ev in all_events])

    # One event time ought to be enough to check
    selected_event = all_events[0]
    retrieved_time = get_event_time(selected_event)
    assert retrieved_time


expected_beers = [
    "North Coast Cranberry Quince Berliner Weisse (BTL)",
    "Yazoo 16th Anniversary Lager",
    "Rhinegeist Dad",
    "Diskin Bourbon Tart Cherry",
    "Terrapin Moo Hoo Milk Stout",
    "NOLA Sauvage",
    "Perennial Fantastic Voyage",
    "Boulevard Plaid Habit",
    "Radeberger Pilsner",
    "Untitled Art / Equilibrium Espresso Marshmellow Stout",
]


def test_new_arrival_parser():
    provider = LocalFileContentProvider("test_resources/new-arrivals.html")
    parser = NewArrivalsParser(provider)
    beers = [b["name"] for b in parser.parse()]
    assert beers == expected_beers


def test_saucer_site_structure():
    """
    Tests to make sure Saucer didn't change their site
    """
    arrivals = get_new_arrivals("raleigh").split("\n")  # to M & M
    assert len(arrivals) > 0
    assert all(arrivals)
