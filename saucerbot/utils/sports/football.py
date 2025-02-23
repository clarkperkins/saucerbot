import datetime
import logging
import math
from typing import Optional

import arrow
import requests

from saucerbot.utils.sports.models import VandyResult, Team

logger = logging.getLogger(__name__)


ESPN_FOOTBALL_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    "?lang=en&region=us&calendartype=blacklist&limit=300&dates={year}"
    "&seasontype={season}&week={week}&groups=80"
)


class VandyFootball(Team):

    def __init__(self):
        super().__init__('Vandy Football')

    def is_in_season(self, desired_date: arrow.Arrow):
        return desired_date.month >= 8 or desired_date.month <= 2

    def get_latest_result(self, desired_date: arrow.Arrow):
        game_info = get_football_results(desired_date)
        if game_info is None:
            return None
        vandy, opponent = self.__get_teams(game_info)
        return VandyResult(
            date=arrow.get(game_info['date']).date(),
            opponent_name=opponent["team"]["displayName"],
            opponent_score=opponent["score"],
            vandy_team=self.name,
            vandy_score=vandy["score"],
            is_finished=game_info["status"]["type"]["completed"]
        )

    def has_match_in_message(self, message: str) -> bool:
        return False

    @staticmethod
    def __get_teams(game: dict) -> tuple[dict, dict]:
        """
        Extracts the teams from the game. Vandy will be returned first
        :param game: the game information
        :return: both teams, vandy first
        """
        team1 = game["competitions"][0]["competitors"][0]
        team2 = game["competitions"][0]["competitors"][1]
        if team1["team"]["location"] == "Vanderbilt":
            return team1, team2
        else:
            return team2, team1


def get_football_results(desired_date: arrow.Arrow) -> Optional[dict]:
    logger.debug("Getting the football results")
    if (
        1 < desired_date.month < 8
    ):  # don't really care to do football if it's February-July
        return None
    if (desired_date.month == 12 and desired_date.day > 11) or desired_date.month == 1:
        # if it's after Dec. 11, then it's a bowl game
        season_type = 3  # code for bowl season
        week = 1
    else:
        season_type = 2  # code for regular season
        week = __get_week(desired_date)
        logger.debug("It's week %i", week)
    url = ESPN_FOOTBALL_URL.format(
        year=desired_date.year, week=week, season=season_type
    )
    logger.debug("Requesting URL '%s'", url)
    response = requests.get(url)
    if 200 <= response.status_code < 300:
        scores = response.json()
        game = __get_the_dores_game(scores)
        return game
    else:
        logger.warning(
            "Received non-success response code: %i -- %s",
            response.status_code,
            response.text,
        )
        return None


def __get_the_dores_game(scores: dict) -> dict | None:
    for ev in scores["events"]:
        teams = ev["competitions"][0]["competitors"]
        for team in teams:
            if team["team"]["location"] == "Vanderbilt":
                return ev
    logger.info("Looked through all the events, couldn't find the Vandy game")
    return None


def __get_week(desired_date: arrow.Arrow) -> int:
    """
    We're gonna assume that week 1 is always Labor Day  (which, in older seasons before
    like 2007 wasn't the case, so we may need a better method for this in the future)
    :param desired_date: the date we're checking the week from
    :return: the week number
    """
    labor_day = arrow.get(datetime.datetime(desired_date.year, 9, 1), "US/Central")
    while labor_day.weekday() != 0:
        labor_day = labor_day.shift(days=+1)
    # we'll say Thursday is the one we want to calculate from
    week_1 = labor_day.shift(days=-4)
    diff = desired_date - week_1
    week = int(math.floor(diff.days / 7)) + 1
    return week
