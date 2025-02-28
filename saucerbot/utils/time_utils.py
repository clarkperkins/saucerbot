import datetime

import arrow

CENTRAL_TIME = "US/Central"

def get_date_from_string(date: str) -> datetime.date:
    return arrow.get(date).to(CENTRAL_TIME).date()
