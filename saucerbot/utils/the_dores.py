# -*- coding: utf-8 -*-

import datetime
import logging
import math
import random
import sys
from typing import Dict, Optional, Tuple

import arrow
import requests

logger = logging.getLogger(__name__)

ESPN_FOOTBALL_URL = (
    "http://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    "?lang=en&region=us&calendartype=blacklist&limit=300&dates={year}"
    "&seasontype={season}&week={week}&groups=80"
)

WINNING_FORMATS = [
    "Hell yeah! The 'Dores took down the {team} {vandy_score}-{other_score}",
    "ATFD! Vandy rolled past the {team} {vandy_score}-{other_score}",
    "The {team} stood no chance! Vandy wins {vandy_score}-{other_score}",
    "Vandy conquered the {team}, prevailing with a score of {vandy_score}-{other_score}"
]

LOSING_FORMATS = [
    "Not this time... the {team} overcame Vandy {other_score}-{vandy_score}",
    "No :( We lost {other_score}-{vandy_score} to the {team}"
]

IN_PROGRESS_MESSAGES = [
    "Time will tell...",
    "Waiting on the result!",
    "I don't know yet, but go dores!"
]


def get_football_results(desired_date: arrow.Arrow) -> Optional[Dict]:
    logger.debug('Getting the football results')
    if 1 < desired_date.month < 8:  # don't really care to do football if it's February-July
        return None
    if (desired_date.month == 12 and desired_date.day > 11) or desired_date.month == 1:
        # if it's after Dec. 11, then it's a bowl game
        season_type = 3  # code for bowl season
        week = 1
    else:
        season_type = 2  # code for regular season
        week = __get_week(desired_date)
        logger.debug(f"It's week {week}")
    url = ESPN_FOOTBALL_URL.format(year=desired_date.year, week=week, season=season_type)
    logger.debug(f"Requesting URL '{url}'")
    response = requests.get(url)
    if 200 <= response.status_code < 300:
        scores = response.json()
        game = __get_the_dores_game(scores)
        return game
    else:
        logger.warning(f'Received non-success response code: '
                       f'{response.status_code} -- {response.text}')
        return None


def __get_the_dores_game(scores: Dict) -> Optional[Dict]:
    for ev in scores['events']:
        teams = ev['competitions'][0]['competitors']
        for team in teams:
            if team['team']['location'] == 'Vanderbilt':
                return ev
    logger.info("Looked through all the events, couldn't find the Vandy game")
    return None


def __get_teams(game: Dict) -> Tuple[Dict, Dict]:
    """
    Extracts the teams from the game. Vandy will be returned first
    :param game: the game information
    :return: both teams, vandy first
    """
    team1 = game['competitions'][0]['competitors'][0]
    team2 = game['competitions'][0]['competitors'][1]
    if team1['team']['location'] == 'Vanderbilt':
        return team1, team2
    else:
        return team2, team1


def __get_week(desired_date: arrow.Arrow) -> int:
    """
    We're gonna assume that week 1 is always Labor Day  (which, in older seasons before
    like 2007 wasn't the case, so we may need a better method for this in the future)
    :param desired_date: the date we're checking the week from
    :return: the week number
    """
    labor_day = arrow.get(datetime.datetime(desired_date.year, 9, 1), 'US/Central')
    while labor_day.weekday() != 0:
        labor_day = labor_day.shift(days=+1)
    # we'll say Thursday is the one we want to calculate from
    week_1 = labor_day.shift(days=-4)
    diff = desired_date - week_1
    week = int(math.floor(diff.days / 7)) + 1
    return week


def did_the_dores_win(print_in_progress: bool = False, print_loss: bool = False,
                      desired_date: arrow.Arrow = None) -> Optional[str]:
    """
    Checks if the dores won on the desired date! It'll return a response in the case of a win,
    or a loss with the first argument set to true. Right now it only does football, but basketball
    should be pretty easy to incorporate
    :param print_in_progress:
    :param print_loss: if True, will return a message in the event of a loss. If false, None will
        be returned for a loss
    :param desired_date: the date to check the score from
    :return: A String message if Vandy won, then either None or a losing message if we lost,
        depending on the parameter
    """
    if desired_date is None:
        desired_date = arrow.now('US/Central')
    game = get_football_results(desired_date)
    if game is None:
        logger.debug("No game found")
        return None
    else:
        vandy, opponent = __get_teams(game)
        if game['status']['type']['completed'] is False:
            logger.debug("Game still in progress")
            if print_in_progress:
                return random.choice(IN_PROGRESS_MESSAGES)
            else:
                return None
        elif vandy['winner'] is True:
            response = random.choice(WINNING_FORMATS)
        else:
            if print_loss:
                response = random.choice(LOSING_FORMATS)
            else:
                logger.debug("Vandy lost, but no printing is enabled")
                return None
        return response.format(team=opponent['team']['displayName'], vandy_score=vandy['score'],
                               other_score=opponent['score'])


# Good for testing the feature
if __name__ == '__main__':
    if len(sys.argv) > 1:
        date = arrow.get(sys.argv[1], 'MM-DD-YYYY')
    else:
        date = None
    print(did_the_dores_win(True, True, date))
