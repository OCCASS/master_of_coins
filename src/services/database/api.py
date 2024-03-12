from typing import Sequence

from sqlalchemy import and_

from .models import *
from .tools import session_scope


async def create_user(user_id: int, username: str) -> None:
    await User.create(
        id=user_id, username=username, balance=0, misha_balance=0, currency=1
    )


async def create_salary(user: int) -> None:
    await Salary.create(user=user, amount=0, total_amount=0)


async def create_bet20_salary(user: int) -> None:
    await Bet20Salary.create(user=user, amount=0, total_amount=0)


async def create_charity(user: int) -> None:
    await Charity.create(user=user, amount=0, total_amount=0)


async def get_users() -> Sequence[User]:
    return await User.filter(User.active == True)


async def get_salaries() -> Sequence[Salary]:
    async with session_scope() as session:
        q = sa.select(Salary).join(
            User, and_(Salary.user == User.id, User.active == True)
        )
        result = await session.execute(q)
    return result.scalars().all()


async def get_bet20_salaries() -> Sequence[Bet20Salary]:
    async with session_scope() as session:
        q = sa.select(Bet20Salary).join(
            User, and_(Bet20Salary.user == User.id, User.active == True)
        )
        result = await session.execute(q)
    return result.scalars().all()


async def get_user_reports_by_interval(
    user_id: int, start: datetime.datetime, end: datetime.datetime
) -> Sequence[Report]:
    return await Report.filter(
        and_(
            Report.user == user_id,
            Report.created_at >= start,
            Report.created_at <= end,
            Report.active == True,
        )
    )


async def get_partner_reports_by_interval(
    partner_id: int, start: datetime.datetime, end: datetime.datetime
) -> Sequence[Report]:
    return await Report.filter(
        and_(
            Report.partner == partner_id,
            Report.created_at >= start,
            Report.created_at <= end,
            Report.active == True,
        )
    )


async def get_user_reports(user: int) -> Sequence[Report]:
    return await Report.filter(and_(Report.user == user, Report.active == True))


async def get_partners() -> Sequence[Partner]:
    return await Partner.filter(Partner.active == True)


async def create_report(
    user: int,
    photo: str,
    amount: int | float,
    refund_amount: int | float,
    salary_percent: int,
    partner: int,
    erroneous: bool = False,
) -> Report:
    return await Report.create(
        user=user,
        photo=photo,
        amount=amount,
        refund_amount=refund_amount,
        erroneous=erroneous,
        salary_percent=salary_percent,
        partner=partner,
    )


async def create_operation(user: int, amount: int | float, reason: str) -> Operation:
    return await Operation.create(user=user, amount=amount, reason=reason)


async def get_operations_by_interval(
    start: datetime.datetime, end: datetime.datetime
) -> Sequence[Operation]:
    return await Operation.filter(
        and_(Operation.created_at >= start, Operation.created_at <= end)
    )


async def get_not_admin_users() -> Sequence[User]:
    return await User.filter(and_(User.is_admin == False, User.active == True))


async def get_admin_users() -> Sequence[User]:
    return await User.filter(and_(User.is_admin == True, User.active == True))


async def create_partner(name: str) -> None:
    await Partner.create(name=name)


async def get_reports_by_interval(
    start: datetime.datetime, end: datetime.datetime
) -> Sequence[Report]:
    return await Report.filter(
        and_(
            Report.created_at >= start, Report.created_at <= end, Report.active == True
        )
    )


async def get_user_reports_by_partner_and_interval(
    user: int, partner: int, start: datetime.datetime, end: datetime.datetime
) -> Sequence[Report]:
    return await Report.filter(
        and_(
            Report.user == user,
            Report.partner == partner,
            Report.created_at >= start,
            Report.created_at <= end,
            Report.active == True,
        )
    )


async def get_user_reports_by_partner(user: int, partner: int) -> Sequence[Report]:
    return await Report.filter(
        and_(Report.user == user, Report.partner == partner, Report.active == True)
    )


async def deactive_report(report_id: int) -> None:
    report = await Report.get(id=report_id)
    await report.update(active=False)


async def get_charities() -> Sequence[Charity]:
    return await Charity.all()


async def update_user_work_staus(user: int, status: bool) -> None:
    user = await User.get(id=user)
    await user.update(in_work=status)


async def start_work_interval(user: int) -> None:
    await WorkInterval.create(user=user)


async def get_last_work_interval(user: int) -> WorkInterval:
    return await WorkInterval.get(user=user, end_at=None)


async def end_last_work_interval(user: int) -> None:
    last_work_interval = await get_last_work_interval(user)
    await last_work_interval.update(end_at=datetime.datetime.now())
