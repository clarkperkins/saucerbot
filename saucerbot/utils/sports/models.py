import datetime
from abc import ABCMeta
from typing import Optional

import arrow
from pydantic import BaseModel


class VandyResult(BaseModel):
    date: datetime.date
    is_finished: bool
    vandy_team: str
    vandy_score: Optional[int]
    opponent: str
    opponent_score: Optional[int]

    def is_win(self):
        return self.is_finished and self.vandy_score > self.opponent_score

    def is_loss(self):
        return self.is_finished and self.vandy_score < self.opponent_score


# Abstraction for different Vandy teams to get their results
class Team(metaclass=ABCMeta):

    def __init__(self, name: str):
        self.name = name

    def is_in_season(self, desired_date: arrow.Arrow) -> bool:
        raise NotImplementedError()

    def get_latest_result(self, desired_date: arrow.Arrow) -> VandyResult | None:
        raise NotImplementedError()

    def has_match_in_message(self, message: str) -> bool:
        raise NotImplementedError()
