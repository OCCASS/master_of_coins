import datetime

from src.data import settings
from src.services.database.api import (
    get_user_reports_by_interval,
    get_user_reports,
    get_users,
    get_salaries,
    get_charities,
    get_bet20_salaries,
    get_user_reports_by_partner_and_interval,
    get_user_reports_by_partner,
)


async def total_bet20_profit_from(user: int, from_: datetime.datetime | None) -> float:
    if from_ is not None:
        reports = await get_user_reports_by_partner_and_interval(
            user, settings.BET_20_PARTNER_ID, from_, datetime.datetime.now()
        )
    else:
        reports = await get_user_reports_by_partner(user, settings.BET_20_PARTNER_ID)
    return round(sum([r.profit() for r in reports]), 2)


async def total_bet20_amount_from(user: int, from_: datetime.datetime | None) -> float:
    if from_ is not None:
        reports = await get_user_reports_by_partner_and_interval(
            user, settings.BET_20_PARTNER_ID, from_, datetime.datetime.now()
        )
    else:
        reports = await get_user_reports_by_partner(user, settings.BET_20_PARTNER_ID)
    return round(sum([r.amount for r in reports]), 2)


async def get_common_balance() -> float:
    users = await get_users()
    return round(sum([u.balance for u in users]), 2)


async def get_common_misha_balance() -> float:
    users = await get_users()
    return round(sum([u.misha_balance for u in users]), 2)


async def get_common_salary() -> float:
    salaries = await get_salaries()
    return round(sum([s.amount for s in salaries]), 2)


async def get_common_bet20_salary() -> float:
    salaries = await get_bet20_salaries()
    return round(sum([s.amount for s in salaries]), 2)


async def get_common_total_charity() -> float:
    charity = await get_charities()
    return round(sum([c.total_amount for c in charity]), 2)


async def get_common_charity() -> float:
    charity = await get_charities()
    return round(sum([c.amount for c in charity]), 2)
