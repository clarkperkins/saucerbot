import datetime
from typing import Optional


class VandyResult:

    def __init__(self, date: datetime.date, opponent_name: str, is_finished: bool, vandy_score: Optional[int], opponent_score: Optional[int]):
        self.date = date
        self.opponent = opponent_name
        self.is_finished = is_finished
        self.vandy_score = vandy_score
        self.opponent_score = opponent_score

    def is_win(self):
        return self.is_finished and self.vandy_score > self.opponent_score

    def is_loss(self):
        return self.is_finished and self.vandy_score < self.opponent_score
