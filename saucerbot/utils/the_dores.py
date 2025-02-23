# -*- coding: utf-8 -*-

import logging
import random
import sys
from typing import List, Tuple

import arrow

from saucerbot.handlers import Message
from saucerbot.utils.sports.basketball import MensBasketball, WomensBasketball
from saucerbot.utils.sports.football import VandyFootball
from saucerbot.utils.sports.models import VandyResult

logger = logging.getLogger(__name__)

GENERIC_VANDY_NAMES = ['The Dores', 'Vandy', 'The Commodores', 'Vanderbilt']

WINNING_FORMATS = [
    "{vandy_name} took down the {opponent_name} {vandy_score}-{opponent_score}",
    "{vandy_name} rolled past the {opponent_name} {vandy_score}-{opponent_score}",
    "The {opponent_name} stood no chance! {vandy_name} wins {vandy_score}-{opponent_score}",
    "{vandy_name} conquered the {opponent_name}, prevailing with a score of {vandy_score}-{opponent_score}",
    "{vandy_name} beat {opponent_name} {vandy_score}-{opponent_score}. Vandy, we're fuckin turnt!"
]

LOSING_FORMATS = [
    "The {opponent_name} overcame {vandy_name} {opponent_score}-{vandy_score}",
    "{vandy_name} lost {opponent_score}-{vandy_score} to the {opponent_name}",
]

IN_PROGRESS_FORMATS = [
    "Time will tell...",
    "Waiting on the result!",
    "I don't know yet, but go dores!",
]

IN_PROGRESS_FOLLOW_UPS = [
    "Still waiting to find out about {vandy_name} in their game vs {opponent_name}",
    "Stay tuned to find out what happens as {vandy_name} takes on {opponent_name}",
]

WINNING_INTERJECTIONS = ["ATFD!", "Hell yeah!", "Kachow!", "You know it!"]
WINNING_CONJUNCTIONS = ["But that's not all!", "Also!", "Keep the party rolling!"]
LOSING_INTERJECTIONS = ["No :(", "Not this time...", "Welllllll..."]
LOSS_AFTER_WIN_CONJUNCTIONS = ["Buuut,", "Unfortunately though,"]
LOSS_AFTER_LOSS_CONJUNCTIONS = ["And unfortunately", "Ugh! And,"]

VANDY_TEAMS = [VandyFootball(), MensBasketball(), WomensBasketball()]


def did_the_dores_win(
    message: Message = None,
    desired_date: arrow.Arrow = None,
) -> str | None:
    """
    Checks if the dores won on the desired date! It'll return a response in the case of a win,
    or a loss with the first argument set to true. Right now it only does football, but basketball
    should be pretty easy to incorporate
    :param message: the trigger message from the chat
    :param desired_date: the date to check the score from
    :return: A String message if Vandy won, then either None or a losing message if we lost,
        depending on the parameter
    """
    if desired_date is None:
        desired_date = arrow.now("US/Central")

    teams = determine_teams_for_lookup(message, desired_date)
    team_results = [team.get_latest_result(desired_date) for team in teams]

    if len(team_results) == 0:
        logger.debug("No game found")
        return None

    team_results = sort_team_results(team_results, desired_date)
    return build_message_response(team_results)


def determine_teams_for_lookup(message: Message, desired_date: arrow.Arrow):
    if message:
        # if someone asks for them, we report
        matches = [team for team in VANDY_TEAMS if team.has_match_in_message(message.content)]
        if len(matches) > 0:
            return matches

    # if no one's asked for, then we'll report whoever's in season
    return [team for team in VANDY_TEAMS if team.is_in_season(desired_date)]


def sort_team_results(results: List[VandyResult], desired_date: arrow.Arrow):
    # Priority: Date is on or before today, Is a Win, Is Loss,
    # Is still In Progress (or is later today), is in the Future
    def sort_key(result: VandyResult) -> Tuple:
        result_not_in_future = result.date <= desired_date.date()
        return (result_not_in_future, result.date, result.is_win(), result.is_finished)

    return sorted(results, key=sort_key, reverse=True)


def build_message_response(results: List[VandyResult]) -> str:
    response = __build_single_result_response(results[0], len(results) == 1)
    last_result = results[0]
    for result in results[1:]:
        response += "\n" + __build_follow_up_response(result, last_result)
        last_result = result

    return response


def __build_single_result_response(result: VandyResult, is_only_result: bool) -> str:
    if not result.is_finished:
        logger.debug("Game is either later today or still in progress")
        format_string = random.choice(IN_PROGRESS_FORMATS)
    elif result.is_win():
        format_string = random.choice(WINNING_INTERJECTIONS) + " " + random.choice(WINNING_FORMATS)
    else:
        format_string = random.choice(LOSING_INTERJECTIONS) + " " + random.choice(LOSING_FORMATS)

    vandy_team_name = 'Vandy' if is_only_result else result.vandy_team
    return format_string.format(vandy_name=vandy_team_name, vandy_score=result.vandy_score, opponent_name=result.opponent, opponent_score=result.opponent_score)


def __build_follow_up_response(result: VandyResult, last_result: VandyResult) -> str:
    if not result.is_finished:
        format_string = random.choice(IN_PROGRESS_FOLLOW_UPS)
    elif result.is_win():
        format_string = random.choice(WINNING_CONJUNCTIONS) + " " + random.choice(WINNING_FORMATS)
    else:
        conjunction = random.choice(LOSS_AFTER_WIN_CONJUNCTIONS) if last_result.is_win() else random.choice(LOSS_AFTER_LOSS_CONJUNCTIONS)
        format_string = conjunction + " " + random.choice(LOSING_FORMATS)

    return format_string.format(vandy_name=result.vandy_team, vandy_score=result.vandy_score, opponent_name=result.opponent, opponent_score=result.opponent_score)


# Good for testing the feature
if __name__ == "__main__":
    date: arrow.Arrow | None
    if len(sys.argv) > 1:
        date = arrow.get(sys.argv[1], "MM-DD-YYYY")
    else:
        date = None
    print(did_the_dores_win(date))
