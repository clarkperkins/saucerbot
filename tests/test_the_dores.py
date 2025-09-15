from unittest.mock import Mock

import arrow
import pytest

from saucerbot.utils import did_the_dores_win
from saucerbot.utils.sports.basketball import MensBasketball, WomensBasketball
from saucerbot.utils.sports.football import VandyFootball
from saucerbot.utils.sports.models import Team, VandyResult
from saucerbot.utils.the_dores import (
    build_message_response,
    determine_teams_for_lookup,
    sort_team_results,
)


@pytest.fixture(autouse=True)
def replace_options_for_text(monkeypatch):
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.WINNING_FORMATS", ["{vandy_name} win"]
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.IN_PROGRESS_FORMATS", ["{vandy_name} in_prog"]
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.LOSING_FORMATS", ["{vandy_name} loss"]
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.IN_PROGRESS_FOLLOW_UPS",
        ["{vandy_name} in_prog_follow"],
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.WINNING_INTERJECTIONS", ["win_inter"]
    )
    monkeypatch.setattr("saucerbot.utils.the_dores.WINNING_CONJUNCTIONS", ["win_conj"])
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.LOSING_INTERJECTIONS", ["loss_inter"]
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.LOSS_AFTER_WIN_CONJUNCTIONS", ["loss_after_win"]
    )
    monkeypatch.setattr(
        "saucerbot.utils.the_dores.LOSS_AFTER_LOSS_CONJUNCTIONS", ["loss_after_loss"]
    )


@pytest.fixture()
def mock_team_1():
    team_1 = Mock(Team)
    team_1.name = "Team1"
    team_1.is_in_season.return_value = True
    team_1.has_match_in_message.return_value = True
    team_1.get_latest_result.return_value = VandyResult(
        date=arrow.get("2021-01-01").date(),
        is_finished=True,
        vandy_team="Team1",
        vandy_score=30,
        opponent="Opp",
        opponent_score=27,
    )
    return team_1


@pytest.fixture()
def mock_team_2():
    team_2 = Mock(Team)
    team_2.name = "Team2"
    team_2.is_in_season.return_value = True
    team_2.has_match_in_message.return_value = False
    team_2.get_latest_result.return_value = VandyResult(
        date=arrow.get("2021-01-02").date(),
        is_finished=True,
        vandy_team="Team2",
        vandy_score=30,
        opponent="Opp",
        opponent_score=50,
    )
    return team_2


@pytest.fixture()
def mock_team_3():  # never returns results
    team_3 = Mock(Team)
    team_3.name = "Team2"
    team_3.is_in_season.return_value = True
    team_3.has_match_in_message.return_value = False
    team_3.get_latest_result.return_value = None
    return team_3


@pytest.fixture()
def mocked_teams(mock_team_1, mock_team_2, mock_team_3, monkeypatch):
    teams_list = [mock_team_1, mock_team_2, mock_team_3]
    monkeypatch.setattr("saucerbot.utils.the_dores.VANDY_TEAMS", teams_list)
    return teams_list


@pytest.fixture()
def mock_teams_no_message_match(mock_team_2, monkeypatch):
    teams_list = [mock_team_2]
    monkeypatch.setattr("saucerbot.utils.the_dores.VANDY_TEAMS", teams_list)
    return teams_list


# testing by season inclusion
@pytest.mark.parametrize(
    "date,expected_teams",
    [
        (arrow.get("2024-09-01"), [VandyFootball]),  # Football in season
        (
            arrow.get("2024-01-15"),
            [MensBasketball, WomensBasketball, VandyFootball],
        ),  # All in season
        (arrow.get("2024-06-01"), []),  # Offseason for all
        (
            arrow.get("2024-11-15"),
            [MensBasketball, WomensBasketball, VandyFootball],
        ),  # All in season
        (
            arrow.get("2024-04-15"),
            [MensBasketball, WomensBasketball],
        ),  # Basketball in season
    ],
)
def test_determine_teams_for_lookup(date, expected_teams):
    teams = determine_teams_for_lookup(None, date)
    assert {type(team) for team in teams} == set(expected_teams)


# testing for messages explicitly asking for teams
@pytest.mark.parametrize(
    "message,expected_teams",
    [
        ("did vandy win", []),  # no teams called out
        ("did vandy mbb win", [MensBasketball]),
        ("did the vandy men win", [MensBasketball]),
        ("wbb did vandy win", [WomensBasketball]),
        ("did vandy's women win", [WomensBasketball]),
        ("did vandy win at football", [VandyFootball]),
        ("did vandy win their basketball game", [MensBasketball, WomensBasketball]),
    ],
)
def test_determine_teams_for_lookup(message, expected_teams):
    teams = determine_teams_for_lookup(message, arrow.get("2024-07-01"))
    assert {type(team) for team in teams} == set(expected_teams)


@pytest.mark.parametrize(
    "results,expected_order",
    [
        # Sorting by date
        (
            [
                VandyResult(
                    date=arrow.get("2024-09-09").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=21,
                    opponent="Georgia",
                    opponent_score=35,
                ),
                VandyResult(
                    date=arrow.get("2024-09-11").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=24,
                    opponent="LSU",
                    opponent_score=20,
                ),
                VandyResult(
                    date=arrow.get("2024-09-10").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=30,
                    opponent="Alabama",
                    opponent_score=27,
                ),
            ],
            ["LSU", "Alabama", "Georgia"],
        ),
        # Prioritizing wins over losses over in-progress games
        (
            [
                VandyResult(
                    date=arrow.get("2024-09-11").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=21,
                    opponent="Georgia",
                    opponent_score=35,
                ),
                VandyResult(
                    date=arrow.get("2024-09-11").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=30,
                    opponent="Alabama",
                    opponent_score=27,
                ),
                VandyResult(
                    date=arrow.get("2024-09-11").date(),
                    is_finished=False,
                    vandy_team="Vandy Football",
                    vandy_score=14,
                    opponent="Florida",
                    opponent_score=14,
                ),
            ],
            ["Alabama", "Georgia", "Florida"],
        ),
        # Prioritizing wins, then date
        (
            [
                VandyResult(
                    date=arrow.get("2024-09-10").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=21,
                    opponent="Missouri",
                    opponent_score=35,
                ),
                VandyResult(
                    date=arrow.get("2024-09-11").date(),
                    is_finished=False,
                    vandy_team="Vandy Football",
                    vandy_score=14,
                    opponent="Texas",
                    opponent_score=14,
                ),
                VandyResult(
                    date=arrow.get("2024-09-09").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=30,
                    opponent="Alabama",
                    opponent_score=27,
                ),
            ],
            ["Alabama", "Texas", "Missouri"],
        ),
        # Future event handling
        (
            [
                VandyResult(
                    date=arrow.get("2024-09-10").date(),
                    is_finished=True,
                    vandy_team="Vandy Football",
                    vandy_score=30,
                    opponent="Alabama",
                    opponent_score=27,
                ),
                VandyResult(
                    date=arrow.get("2024-09-15").date(),
                    is_finished=False,
                    vandy_team="Vandy Football",
                    vandy_score=0,
                    opponent="Tennessee",
                    opponent_score=0,
                ),
            ],
            ["Alabama", "Tennessee"],
        ),
    ],
)
def test_sort_team_results(results, expected_order):
    sorted_results = sort_team_results(results, arrow.get("2024-09-11"))
    assert [result.opponent for result in sorted_results] == expected_order


def test_build_message_response_one_result():
    results = [
        VandyResult(
            date=arrow.now().date(),
            is_finished=True,
            vandy_team="Vandy Football",
            vandy_score=30,
            opponent="Alabama",
            opponent_score=27,
        )
    ]
    result = build_message_response(results)
    assert "win_inter Vandy win" in result


def test_build_message_response_two_wins():
    results = [
        VandyResult(
            date=arrow.get("2024-09-01").date(),
            is_finished=True,
            vandy_team="Vandy Football",
            vandy_score=30,
            opponent="Alabama",
            opponent_score=27,
        ),
        VandyResult(
            date=arrow.get("2024-09-02").date(),
            is_finished=True,
            vandy_team="Vandy Basketball",
            vandy_score=35,
            opponent="Georgia",
            opponent_score=28,
        ),
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "win_conj Vandy Basketball win" in result


def test_build_message_response_win_loss():
    results = [
        VandyResult(
            date=arrow.get("2024-09-01").date(),
            is_finished=True,
            vandy_team="Vandy Football",
            vandy_score=55,
            opponent="Alabama",
            opponent_score=35,
        ),
        VandyResult(
            date=arrow.get("2024-09-02").date(),
            is_finished=True,
            vandy_team="Vandy Basketball",
            vandy_score=10,
            opponent="Georgia",
            opponent_score=21,
        ),
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "loss_after_win Vandy Basketball loss" in result


def test_build_message_response_two_losses():
    results = [
        VandyResult(
            date=arrow.get("2024-09-01").date(),
            is_finished=True,
            vandy_team="Vandy Football",
            vandy_score=14,
            opponent="Alabama",
            opponent_score=35,
        ),
        VandyResult(
            date=arrow.get("2024-09-02").date(),
            is_finished=True,
            vandy_team="Vandy Basketball",
            vandy_score=10,
            opponent="Georgia",
            opponent_score=21,
        ),
    ]
    result = build_message_response(results)
    assert "loss_inter Vandy Football loss" in result
    assert "loss_after_loss Vandy Basketball loss" in result


def test_build_message_response_one_win_one_in_progress():
    results = [
        VandyResult(
            date=arrow.get("2024-09-01").date(),
            is_finished=True,
            vandy_team="Vandy Football",
            vandy_score=30,
            opponent="Alabama",
            opponent_score=27,
        ),
        VandyResult(
            date=arrow.get("2024-09-02").date(),
            is_finished=False,
            vandy_team="Vandy Basketball",
            vandy_score=0,
            opponent="Georgia",
            opponent_score=0,
        ),
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "Vandy Basketball in_prog_follow" in result


def test_build_message_response_two_in_progress():
    results = [
        VandyResult(
            date=arrow.get("2024-09-01").date(),
            is_finished=False,
            vandy_team="Vandy Football",
            vandy_score=0,
            opponent="Alabama",
            opponent_score=0,
        ),
        VandyResult(
            date=arrow.get("2024-09-02").date(),
            is_finished=False,
            vandy_team="Vandy Basketball",
            vandy_score=0,
            opponent="Georgia",
            opponent_score=0,
        ),
    ]
    result = build_message_response(results)
    assert "Vandy Football in_prog" in result
    assert "Vandy Basketball in_prog_follow" in result


@pytest.mark.parametrize(
    "message,desired_date,result_text",
    [
        (
            None,
            arrow.get("2021-01-03"),
            "win_inter Team1 win\n\nloss_after_win Team2 loss",
        ),
        (
            None,
            arrow.get("2021-01-04"),
            "loss_inter Vandy loss",
        ),  # within 3 days for team 2
        (
            "Message",
            arrow.get("2021-01-03"),
            "win_inter Vandy win",
        ),  # has message match for team 1
        (
            "Message",
            arrow.get("2021-01-06"),
            None,
        ),  # message match, but beyond acceptable date
        (None, arrow.get("2021-01-10"), None),  # no matches at all
    ],
)
def test_the_whole_thing_no_message(mocked_teams, message, desired_date, result_text):
    actual_value = did_the_dores_win(message, desired_date)
    assert actual_value == result_text


# gotta make sure if there's no match, we still run
def test_the_whole_thing_no_message_match(mock_teams_no_message_match):
    actual_value = did_the_dores_win("Message provided", arrow.get("2021-01-03"))
    assert actual_value == "loss_inter Vandy loss"
