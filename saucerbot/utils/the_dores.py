# -*- coding: utf-8 -*-

import logging
import random
import sys

import arrow

from saucerbot.utils.sports.football import get_football_results

logger = logging.getLogger(__name__)


WINNING_FORMATS = [
    "Hell yeah! The 'Dores took down the {team} {vandy_score}-{opponent_score}",
    "ATFD! Vandy rolled past the {team} {vandy_score}-{opponent_score}",
    "The {team} stood no chance! Vandy wins {vandy_score}-{opponent_score}",
    "Vandy conquered the {team}, prevailing with a score of {vandy_score}-{opponent_score}",
]

LOSING_FORMATS = [
    "Not this time... the {team} overcame Vandy {opponent_score}-{vandy_score}",
    "No :( We lost {opponent_score}-{vandy_score} to the {team}",
]

IN_PROGRESS_MESSAGES = [
    "Time will tell...",
    "Waiting on the result!",
    "I don't know yet, but go dores!",
]


def did_the_dores_win(
    print_in_progress: bool = False,
    print_loss: bool = False,
    desired_date: arrow.Arrow | None = None,
) -> str | None:
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
        desired_date = arrow.now("US/Central")
    result = get_football_results(desired_date)
    if result is None:
        logger.debug("No game found")
        return None
    else:
        if not result.is_finished:
            logger.debug("Game is either later today or still in progress")
            if print_in_progress:
                return random.choice(IN_PROGRESS_MESSAGES)
            else:
                return None
        elif result.is_win():
            response = random.choice(WINNING_FORMATS)
        else:
            if print_loss:
                response = random.choice(LOSING_FORMATS)
            else:
                logger.debug("Vandy lost, but no printing is enabled")
                return None
        return response.format(
            team=result.opponent,
            vandy_score=result.vandy_score,
            opponent_score=result.opponent_score,
        )


# Good for testing the feature
if __name__ == "__main__":
    date: arrow.Arrow | None
    if len(sys.argv) > 1:
        date = arrow.get(sys.argv[1], "MM-DD-YYYY")
    else:
        date = None
    print(did_the_dores_win(True, True, date))
