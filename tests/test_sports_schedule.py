import json
import random
from datetime import datetime

import arrow
import pytest

from saucerbot.utils.sports.schedule_page_utils import find_most_recent_event, read_schedule_events

simple_events = [{
    "date": {
        "date": "2024-11-14T01:00Z",
    },
    "opponent": {
        "id": "25",
        "abbrev": "CAL",
        "displayName": "California Golden Bears",
        "shortDisplayName": "California Golden Bears",
        "recordSummary": "",
        "standingSummary": "",
        "nickname": "California",
    },
    "result": {
        "winner": True,
        "isTie": False,
        "winLossSymbol": "W",
        "currentTeamScore": "85",
        "opponentTeamScore": "69",
        "statusId": "3"
    },
    "status": {
        "id": "3",
        "name": "STATUS_FINAL",
        "state": "post",
        "completed": True,
    }
}]

simple_espn_fitt = {"page": {"content": {"scheduleData": {"teamSchedule": [{"events": {"post": simple_events}}]}}}}

simple_schedule_html = """
<html>
  <script>
    window['CONFIG']={{"config": "a"}};
    window['__espnfitt__']={config_json};
  </script>
</html>""".format(config_json=json.dumps(simple_espn_fitt))


@pytest.fixture
def sample_events():
    dates_for_events = [datetime(2024, 1, 1), datetime(2024, 3, 1), datetime(2024, 6, 1), datetime(2024, 6, 2)]
    opponents = ['Western KenSUCK-y', 'Presbyterian Blue Hoes', 'One of the 3 SEC Tiger schools', 'The Refs']
    results = [True, True, True, False]

    def make_event(date, opponent, result):
        return {
            'date': date.date(),
            'opponent': {'displayName': opponent},
            'result': {'isWinner': result, 'currentTeamScore': 50, 'opponentTeamScore': 40 + (0 if result else 20)},
            'status': {'completed': True}
        }

    return [make_event(dates_for_events[i], opponents[i], results[i]) for i in range(0, len(dates_for_events))]


def test_read_simple_events():
    events = read_schedule_events(simple_schedule_html)
    assert len(events) == 1

    assert events[0]['date'] == datetime(2024, 11, 14).date()
    assert 'opponent' in events[0]
    assert 'result' in events[0]
    assert 'status' in events[0]


def test_sample_event_page():
    with open('test_resources/sample_schedule_page.html', 'r') as infile:
        html = infile.read()

    events = read_schedule_events(html)
    assert len(events) == 6

    expected_dates = [datetime(2024, 11, 5), datetime(2024, 11, 10), datetime(2024, 11, 14), datetime(2025, 2, 12),
                      datetime(2025, 2, 15), datetime(2025, 2, 20)]

    actual_dates = sorted([event['date'] for event in events])
    expected_dates = sorted([event.date() for event in expected_dates])

    assert actual_dates == expected_dates


@pytest.mark.parametrize('desired_date,expected_result_date', [
    (arrow.Arrow(2024, 2, 1), datetime(2024, 1, 1)),
    (arrow.Arrow(2024, 8, 1), datetime(2024, 6, 2)),  # the last in list
    (arrow.Arrow(2024, 3, 1), datetime(2024, 3, 1)),  # on the day of
    (arrow.Arrow(2024, 6, 1), datetime(2024, 6, 1)),  # consecutive dates, day 1
    (arrow.Arrow(2024, 6, 2), datetime(2024, 6, 2)),  # consecutive dates, day 2
])
def test_find_recent_event(sample_events, desired_date, expected_result_date):
    event = find_most_recent_event(sample_events, desired_date)

    assert event['date'] == expected_result_date.date()


def test_find_recent_event_from_unordered(sample_events):
    desired_date = arrow.Arrow(2024, 2, 1)

    random.shuffle(sample_events)
    event = find_most_recent_event(sample_events, desired_date)

    assert event['date'] == datetime(2024, 1, 1).date()


def test_find_recent_event_none_before(sample_events):
    desired_date = arrow.Arrow(2023, 1, 1)

    event = find_most_recent_event(sample_events, desired_date)

    assert event is None
