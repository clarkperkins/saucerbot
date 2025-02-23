import arrow
import pytest

from saucerbot.utils.sports.basketball import MensBasketball, WomensBasketball
from saucerbot.utils.sports.football import VandyFootball
from saucerbot.utils.sports.models import VandyResult
from saucerbot.utils.the_dores import determine_teams_for_lookup, sort_team_results, build_message_response


@pytest.fixture()
def replace_options_for_text(monkeypatch):
    monkeypatch.setattr("saucerbot.utils.the_dores.WINNING_FORMATS", ["{vandy_name} win"])
    monkeypatch.setattr("saucerbot.utils.the_dores.IN_PROGRESS_FORMATS", ["{vandy_name} in_prog"])
    monkeypatch.setattr("saucerbot.utils.the_dores.LOSING_FORMATS", ["{vandy_name} loss"])
    monkeypatch.setattr("saucerbot.utils.the_dores.IN_PROGRESS_FOLLOW_UPS", ["{vandy_name} in_prog_follow"])
    monkeypatch.setattr("saucerbot.utils.the_dores.WINNING_INTERJECTIONS", ["win_inter"])
    monkeypatch.setattr("saucerbot.utils.the_dores.WINNING_CONJUNCTIONS", ["win_conj"])
    monkeypatch.setattr("saucerbot.utils.the_dores.LOSING_INTERJECTIONS", ["loss_inter"])
    monkeypatch.setattr("saucerbot.utils.the_dores.LOSS_AFTER_WIN_CONJUNCTIONS", ["loss_after_win"])
    monkeypatch.setattr("saucerbot.utils.the_dores.LOSS_AFTER_LOSS_CONJUNCTIONS", ["loss_after_loss"])


# testing by season inclusion
@pytest.mark.parametrize("date,expected_teams", [
    (arrow.get("2024-09-01"), [VandyFootball]),  # Football in season
    (arrow.get("2024-01-15"), [MensBasketball, WomensBasketball, VandyFootball]),  # All in season
    (arrow.get("2024-06-01"), []),  # Offseason for all
    (arrow.get("2024-11-15"), [MensBasketball, WomensBasketball, VandyFootball]),  # All in season
    (arrow.get("2024-04-15"), [MensBasketball, WomensBasketball])  # Basketball in season
])
def test_determine_teams_for_lookup(date, expected_teams):
    teams = determine_teams_for_lookup(None, date)
    assert {type(team) for team in teams} == set(expected_teams)


# testing for messages explicitly asking for teams
@pytest.mark.parametrize("message,expected_teams", [
    ("did vandy win", []),  # no teams called out
    ("did vandy mbb win", [MensBasketball]),
    ("did the vandy men win", [MensBasketball]),
    ("wbb did vandy win", [WomensBasketball]),
    ("did vandy's women win", [WomensBasketball]),
    ("did vandy win at football", [VandyFootball]),
    ("did vandy win their basketball game", [MensBasketball, WomensBasketball])
])
def test_determine_teams_for_lookup(message, expected_teams):
    teams = determine_teams_for_lookup(message, arrow.get("2024-07-01"))
    assert {type(team) for team in teams} == set(expected_teams)


@pytest.mark.parametrize("results,expected_order", [
    # Sorting by date
    ([
        VandyResult(arrow.get("2024-09-09").date(), True, "Vandy Football", 21, "Georgia", 35),
        VandyResult(arrow.get("2024-09-11").date(), True, "Vandy Football", 24, "LSU", 20),
        VandyResult(arrow.get("2024-09-10").date(), True, "Vandy Football", 30, "Alabama", 27)
    ], ["LSU", "Alabama", "Georgia"]),
    # Prioritizing wins over losses over in-progress games
    ([
        VandyResult(arrow.get("2024-09-11").date(), True, "Vandy Football", 21, "Georgia", 35),
        VandyResult(arrow.get("2024-09-11").date(), True, "Vandy Football", 30, "Alabama", 27),
        VandyResult(arrow.get("2024-09-11").date(), False, "Vandy Football", 14, "Florida", 14)
    ], ["Alabama", "Georgia", "Florida"]),
    # Prioritizing wins, then date
    ([
        VandyResult(arrow.get("2024-09-10").date(), True, "Vandy Football", 21, "Missouri", 35),
        VandyResult(arrow.get("2024-09-11").date(), False, "Vandy Football", 14, "Texas", 14),
        VandyResult(arrow.get("2024-09-09").date(), True, "Vandy Football", 30, "Alabama", 27),
    ], ["Alabama", "Texas", "Missouri"]),
    # Future event handling
    ([
        VandyResult(arrow.get("2024-09-10").date(), True, "Vandy Football", 30, "Alabama", 27),
        VandyResult(arrow.get("2024-09-15").date(), False, "Vandy Football", 0, "Tennessee", 0)
    ], ["Alabama", "Tennessee"]),
])
def test_sort_team_results(results, expected_order):
    sorted_results = sort_team_results(results, arrow.get("2024-09-11"))
    assert [result.opponent for result in sorted_results] == expected_order


def test_build_message_response_one_result(replace_options_for_text):
    results = [
        VandyResult(arrow.now().date(), True, "Vandy Football", 30, "Alabama", 27)
    ]
    result = build_message_response(results)
    assert "win_inter Vandy win" in result


def test_build_message_response_two_wins(replace_options_for_text):
    results = [
        VandyResult(arrow.get("2024-09-01").date(), True, "Vandy Football", 30, "Alabama", 27),
        VandyResult(arrow.get("2024-09-02").date(), True, "Vandy Basketball", 35, "Georgia", 28)
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "win_conj Vandy Basketball win" in result


def test_build_message_response_win_loss(replace_options_for_text):
    results = [
        VandyResult(arrow.get("2024-09-01").date(), True, "Vandy Football", 55, "Alabama", 35),
        VandyResult(arrow.get("2024-09-02").date(), True, "Vandy Basketball", 10, "Georgia", 21)
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "loss_after_win Vandy Basketball loss" in result


def test_build_message_response_two_losses(replace_options_for_text):
    results = [
        VandyResult(arrow.get("2024-09-01").date(), True, "Vandy Football", 14, "Alabama", 35),
        VandyResult(arrow.get("2024-09-02").date(), True, "Vandy Basketball", 10, "Georgia", 21)
    ]
    result = build_message_response(results)
    assert "loss_inter Vandy Football loss" in result
    assert "loss_after_loss Vandy Basketball loss" in result


def test_build_message_response_one_win_one_in_progress(replace_options_for_text):
    results = [
        VandyResult(arrow.get("2024-09-01").date(), True, "Vandy Football", 30, "Alabama", 27),
        VandyResult(arrow.get("2024-09-02").date(), False, "Vandy Basketball", 0, "Georgia", 0)
    ]
    result = build_message_response(results)
    assert "win_inter Vandy Football win" in result
    assert "Vandy Basketball in_prog_follow" in result


def test_build_message_response_two_in_progress(replace_options_for_text):
    results = [
        VandyResult(arrow.get("2024-09-01").date(), False, "Vandy Football", 0, "Alabama", 0),
        VandyResult(arrow.get("2024-09-02").date(), False, "Vandy Basketball", 0, "Georgia", 0)
    ]
    result = build_message_response(results)
    assert "Vandy Football in_prog" in result
    assert "Vandy Basketball in_prog_follow" in result
