import json
import logging
from typing import List, Optional

import arrow
import requests

from saucerbot.utils.sports.models import VandyResult

logger = logging.getLogger(__name__)

# different strategy here, just gonna pull the whole schedule and read the page config rather than try to get it by date
# probably could do the scoreboard way, but football has its whole week calculation nonsense; this seemed easier
SCHEDULE_PAGE_START_MARKER = "window['__espnfitt__']"

# It checks for a User-Agent, so whatever, I'll lie to ESPN
HEADERS_FOR_ESPN = {"Accept": "*/*", "User-Agent": "curl/8.7.1"}


def get_schedule_page_results(url: str, desired_date: arrow.Arrow) -> dict | None:
    try:
        logger.info(f"Retrieving latest event from schedule page: {url}")
        schedule = read_schedule_events(request_schedule_page(url))
        most_recent = find_most_recent_event(schedule, desired_date)
        if most_recent:
            logger.info(f"Found most recent event with date {str(most_recent['date'])}")
        else:
            logger.info("No recent events found")
        return most_recent
    except Exception as e:
        logger.error("Failed to read schedule page data", exc_info=e)
        return None


def request_schedule_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS_FOR_ESPN)
    if not (200 <= response.status_code < 300):
        logger.warning(
            "Received non-success response code: %i -- %s",
            response.status_code,
            response.text,
        )
        raise Exception(
            f"Failed to request basketball data from ESPN: {response.status_code}"
        )
    return response.text


def find_most_recent_event(
    events: List[dict], desired_date: arrow.Arrow
) -> Optional[dict]:
    desired_date_casted = (
        desired_date.date()
    )  # make the types match, and just get the date info
    sorted_events = sorted(events, key=lambda x: x["date"])
    if desired_date_casted < sorted_events[0]["date"]:
        return None
    latest_match = sorted_events[0]
    # binary search is for nerds
    for event in sorted_events[1:]:
        if event["date"] > desired_date_casted:
            return latest_match
        else:
            latest_match = event
    return latest_match


def read_schedule_events(response_text: str) -> List[dict]:
    data = __retrieve_basketball_json(response_text)
    seasons = data["page"]["content"]["scheduleData"]["teamSchedule"]
    return [event for season in seasons for event in __read_events(season)]


def __read_events(season: dict) -> List[dict]:
    def parse_event(event: dict) -> dict:
        return {
            "opponent": event["opponent"],
            "date": arrow.get(event["date"]["date"]).date(),
            "result": event["result"],
            "status": event["status"],
        }

    event_map = season["events"]
    event_list = []
    for key, values in event_map.items():
        event_list.extend([parse_event(event) for event in values])

    logger.debug(f"Found {len(event_list)} events")
    return event_list


# yeah it's not as elegant as consuming an API but whatever I'm lazy
def __retrieve_basketball_json(response_text: str) -> dict:
    start = response_text.index(SCHEDULE_PAGE_START_MARKER)
    true_start = response_text.index("{", start)
    end = response_text.index("</script>", start)
    true_end = response_text.rindex("}", start, end)

    logger.debug(
        f"Thinking we have the start of basketball data at {true_start} and the end at {true_end}"
    )
    return json.loads(response_text[true_start : true_end + 1])
