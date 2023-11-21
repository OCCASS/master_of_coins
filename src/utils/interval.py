import datetime

from dataclasses import dataclass


@dataclass
class DateInterval:
    start: datetime.datetime
    end: datetime.datetime


def get_today_interval() -> DateInterval:
    now = datetime.datetime.now()
    return DateInterval(
        start=now.replace(hour=0, minute=0, second=0),
        end=now.replace(hour=23, minute=59, second=59),
    )
