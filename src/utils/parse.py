import datetime
import logging

from .interval import DateInterval


def parse_date_interval(s: str) -> DateInterval | None:
    s = s.replace(" ", "")
    parts = s.split("-")
    if len(parts) != 2:
        return None
    p1, p2 = parts
    try:
        d1 = datetime.datetime.strptime(p1, "%d.%m.%y")
        d2 = datetime.datetime.strptime(p2, "%d.%m.%y")
        d1 = d1.replace(hour=0, minute=0, second=0)
        d2 = d2.replace(hour=23, minute=59, second=59)
        return DateInterval(d1, d2)
    except ValueError:
        return None
    except Exception as e:
        logging.error(e)
        return None


def get_current_month_interval() -> DateInterval:
    now = datetime.datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0)
    end = start.replace(
        month=start.month % 12 + 1, hour=23, minute=59, second=59
    ) - datetime.timedelta(days=1)
    return DateInterval(start, end)
