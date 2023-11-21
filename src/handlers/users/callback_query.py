from aiogram import types
from aiogram.dispatcher import FSMContext

from src.states import States
from src.data import settings
from src.loader import dp
from src.utils.send import send_message, send_confirm_report
from src.keyboards.inline.callbacks import select_partner, confirm_report
from src.services.database.api import create_report, get_user_reports_by_interval
from src.services.database.models import Partner, User, Currency
from src.services.calc import (
    total_profit_from,
    total_bet_amount_from,
    get_common_total_charity,
)
from src.services.templates import render_template
from src.services.forms import start_form, confirm_form, balance_form, today_form
from src.utils.interval import get_today_interval


@dp.callback_query_handler(
    today_form.callback_data().filter(), state=States.UserReports.date
)
async def handle_user_reports_today_date(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    interval = get_today_interval()
    reports = await get_user_reports_by_interval(
        query.from_user.id, interval.start, interval.end
    )
    user = await User.get(id=query.from_user.id)
    currency = await user.get_currency()

    if len(reports) == 0:
        await send_message(render_template("no_reports.j2"))

    for report in reports:
        partner = await report.get_partner()
        await send_message(
            render_template(
                "report.j2",
                context={"report": report, "partner": partner, "currency": currency},
            ),
            photo=report.photo,
        )
    await state.reset_state(with_data=True)


@dp.callback_query_handler(select_partner.filter(), state=States.CreateReport.partner)
async def handle_create_report_partner(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    partner_id = int(callback_data.get("id", -1))

    if partner_id != settings.BET_20_PARTNER_ID:
        await send_message(
            render_template(
                "create_report/salary_percent.j2",
                context={
                    "min": settings.MIN_SALARY_PERCENT,
                    "max": settings.MAX_SALARY_PERCENT,
                },
            )
        )
        await state.update_data(partner=partner_id)
        await state.set_state(States.CreateReport.salary_percent)
    else:
        data = await state.get_data()
        partner = await Partner.get(id=partner_id)
        currency = await Currency.get(id=data.get("currency"))
        await send_confirm_report(
            data.get("amount", 0),
            data.get("refund_amount", 0),
            0,
            data.get("photo", ""),
            partner,
            currency,
            data.get("erroneous", False),
        )
        await state.update_data(partner=partner_id, salary_percent=0)
        await state.set_state(States.CreateReport.confirm)


@dp.callback_query_handler(confirm_report.filter(), state=States.CreateReport.confirm)
async def handle_create_report_confirm(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case confirm_form.accept:
            data = await state.get_data()
            user = await User.get(id=query.from_user.id)
            currency = await user.get_currency()
            salary_percent = data.get("salary_percent", 0)
            partner = data.get("partner", 0)
            erroneous = data.get("erroneous", False)
            report = await create_report(
                query.from_user.id,
                data.get("photo", ""),
                currency.convert_to_eur(data.get("amount", 0)),
                currency.convert_to_eur(data.get("refund_amount", 0)),
                salary_percent,
                partner,
                erroneous,
            )

            if partner == settings.BET_20_PARTNER_ID:
                salary = await user.get_bet20_salary()
                salary_fraction = settings.BET_20_SALARY_FRACTION
            else:
                salary = await user.get_salary()
                salary_fraction = salary_percent / 100
            # process report as erroneous
            if erroneous:
                salary_fraction = 0
                if report.profit() < 0:
                    # fine amount < 0, because report.profit() < 0
                    fine_amount = report.profit() * 3 * settings.DEFAULT_SALARY_FRACTION
                    salary = await user.get_salary()
                    await salary.update(amount=salary.amount + fine_amount)
            else:
                # update user salary
                update_amount = float(report.profit()) * salary_fraction
                await salary.update(
                    amount=salary.amount + update_amount,
                    total_amount=salary.total_amount + update_amount,
                )

            # update user balance to report profit
            await user.update(balance=user.balance + float(report.profit()))
            if partner == settings.MISHA_PARTNER_ID:
                await user.update(
                    misha_balance=user.misha_balance + float(report.profit()) * 0.5
                )
            # update charity balance
            charity = await user.get_charity()
            update_amount = report.amount * settings.CHARITY_FRACTION
            await charity.update(
                amount=charity.amount + update_amount,
                total_amount=charity.total_amount + update_amount,
            )
            await send_message(render_template("create_report/created.j2"))
        case confirm_form.reject:
            await send_message(render_template("create_report/rejected.j2"))

    await send_message(
        render_template("greeting.j2", context={"username": query.from_user.username}),
        reply_markup=start_form.get_inline_keyboard(rows_template=(1, 2)),
    )
    await state.reset_state(with_data=True)


@dp.callback_query_handler(balance_form.callback_data().filter(), state="*")
async def handle_balance_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    option_id = callback_data.get("id")

    user = await User.get(id=query.from_user.id)
    currency = await user.get_currency()
    match option_id:
        case balance_form.balance:
            await send_message(
                render_template(
                    "balance.j2", context={"user": user, "currency": currency}
                )
            )
        case balance_form.salary:
            salary = await user.get_salary()
            bet20_salary = await user.get_bet20_salary()
            total_profit = await total_profit_from(
                user.id, bet20_salary.last_debiting_at
            )
            total_bet_amount = await total_bet_amount_from(
                user.id, bet20_salary.last_debiting_at
            )
            await send_message(
                render_template(
                    "salary.j2",
                    context={
                        "salary": salary,
                        "bet20_salary": bet20_salary,
                        "currency": currency,
                        "total_profit": total_profit,
                        "total_bet_amount": total_bet_amount,
                    },
                )
            )
        case balance_form.create_operation:
            await query.message.delete_reply_markup()
            await send_message(
                render_template(
                    "create_operation/amount.j2", context={"currency": currency}
                )
            )
            await state.set_state(States.CreateOperation.amount)
        case balance_form.charity:
            charity = await user.get_charity()
            common_charity = await get_common_total_charity()
            await send_message(
                render_template(
                    "charity.j2",
                    context={
                        "charity": charity,
                        "currency": currency,
                        "common_total_amount": common_charity,
                    },
                )
            )


@dp.callback_query_handler(start_form.callback_data().filter(), state="*")
async def handle_start_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case start_form.reports:
            await send_message(
                render_template("enter_date.j2"),
                reply_markup=today_form.get_inline_keyboard(),
            )
            await state.set_state(States.UserReports.date)
        case start_form.create_report:
            await send_message(render_template("create_report/photo.j2"))
            await state.update_data(erroneous=False)
            await state.set_state(States.CreateReport.photo)
        case start_form.create_erroneous_report:
            await send_message(render_template("create_report/photo.j2"))
            await state.update_data(erroneous=True)
            await state.set_state(States.CreateReport.photo)
