import arrow
from saucerbot.utils.sports.football import get_week


def test_get_week():
    # Test cases for different dates
    test_cases = [
        (arrow.get("2024-09-01"), 1),  # Labor Day week
        (arrow.get("2024-10-01"), 5),  # Week 5
        (arrow.get("2025-09-01"), 1),  # Labor Day, but Monday
        (arrow.get("2025-09-01"), 1),  # Labor Day, but Monday
    ]

    for date, expected_week in test_cases:
        assert get_week(date) == expected_week, f"Failed for date: {date}"