import logging

from arrow import arrow

from saucerbot.utils.sports.models import Team, VandyResult
from saucerbot.utils.sports.schedule_page_utils import get_schedule_page_results

ESPN_MENS_BASKETBALL_URL = "https://www.espn.com/mens-college-basketball/team/schedule/_/id/238/vanderbilt-commodores"
ESPN_WOMENS_BASKETBALL_URL = "https://www.espn.com/womens-college-basketball/team/schedule/_/id/238"

logger = logging.getLogger(__name__)


class MensBasketball(Team):

    def __init__(self):
        super().__init__("Vandy Men's Basketball")

    def is_in_season(self, desired_date: arrow.Arrow) -> bool:
        return desired_date.month > 10 or desired_date.month < 5

    def get_latest_result(self, desired_date: arrow.Arrow):
        result = get_schedule_page_results(ESPN_MENS_BASKETBALL_URL, desired_date)
        return _get_vandy_result_from_schedule_event(self.name, result)

    def has_match_in_message(self, message: str) -> bool:
        return False


class WomensBasketball(Team):

    def __init__(self):
        super().__init__("Vandy Women's Basketball")

    def is_in_season(self, desired_date: arrow.Arrow) -> bool:
        return desired_date.month > 10 or desired_date.month < 5

    def get_latest_result(self, desired_date: arrow.Arrow):
        result = get_schedule_page_results(ESPN_WOMENS_BASKETBALL_URL, desired_date)
        return _get_vandy_result_from_schedule_event(self.name, result)

    def has_match_in_message(self, message: str) -> bool:
        return False


def _get_vandy_result_from_schedule_event(team_name: str, event: dict) -> VandyResult | None:
    if event is None:
        return None

    return VandyResult(
        date=event['date'],
        opponent_name=event['opponent']['displayName'],
        opponent_score=event['result'].get('opponentTeamScore'),
        vandy_team=team_name,
        vandy_score=event['result'].get('currentTeamScore'),  # no guarantee that there are scores
        is_finished=event['status']['isCompleted']
    )
