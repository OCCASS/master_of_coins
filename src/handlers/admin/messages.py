import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext

from src.loader import dp, bot
from src.data import enums, settings
from src.services.database.api import (
    get_user_reports_by_interval,
    get_partner_reports_by_interval,
    create_operation,
    get_operations_by_interval,
    create_partner,
    get_reports_by_interval,
)
from src.services.database.models import User, Salary, Bet20Salary
from src.services.templates import render_template
from src.services.forms.admin import delete_report_form
from src.services import excel
from src.keyboards.inline.callbacks import delete_report
from src.states import States
from src.utils.parse import parse_date_interval
from src.utils.send import send_message
from src.utils.validate import is_float


@dp.message_handler(state=States.Admin.Other.ManagePartners.Add.name, is_admin=True)
async def handle_add_partner_name(message: types.Message, state: FSMContext):
    await create_partner(message.text)
    await send_message(render_template("admin/partner_created.j2"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Reports.User.date, is_admin=True)
async def handle_user_reports_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return
    data = await state.get_data()
    user_id = data.get("user_id", 0)
    reports = await get_user_reports_by_interval(user_id, interval.start, interval.end)
    if len(reports) == 0:
        await send_message(render_template("no_reports.j2"))

    for r in reports:
        partner = await r.get_partner()
        user = await r.get_user()
        await send_message(
            render_template(
                "admin/report.j2",
                context={"report": r, "partner": partner, "user": user},
            ),
            photo=r.photo,
            reply_markup=delete_report_form.get_inline_keyboard(
                callback_data=delete_report, callback_data_args={"report_id": r.id}
            ),
        )
    excel_file = await excel.create_reports_excel(reports)
    await bot.send_document(message.chat.id, open(excel_file, "rb"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Accounting.ChairtyReport.date, is_admin=True)
async def handle_charity_report_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return
    reports = await get_reports_by_interval(interval.start, interval.end)
    total = round(sum([r.amount * settings.CHARITY_FRACTION for r in reports]), 2)
    await send_message(
        render_template("admin/charity_report.j2", context={"amount": total})
    )
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Reports.Partner.date, is_admin=True)
async def handle_partner_reports_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return
    data = await state.get_data()
    partner_id = data.get("partner_id", -1)
    if partner_id == -1:
        reports = await get_reports_by_interval(interval.start, interval.end)
    else:
        reports = await get_partner_reports_by_interval(
            partner_id, interval.start, interval.end
        )
    for r in reports:
        partner = await r.get_partner()
        user = await r.get_user()
        await send_message(
            render_template(
                "admin/report.j2",
                context={"report": r, "partner": partner, "user": user},
            ),
            photo=r.photo,
        )
    excel_file = await excel.create_reports_excel(reports)
    await bot.send_document(message.chat.id, open(excel_file, "rb"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Reports.Statistic.date, is_admin=True)
async def handle_reports_statistic_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return

    reports = await get_reports_by_interval(interval.start, interval.end)
    common_turnover = 0
    common_profit = 0
    for r in reports:
        common_turnover += r.amount
        common_profit += r.profit()
    await send_message(
        render_template(
            "admin/reports_statistic.j2",
            context={
                "turnover": common_turnover,
                "profit": common_profit,
                "count": len(reports),
            },
        )
    )
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Other.IssueBalance.amount, is_admin=True)
async def handle_issue_balance_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("integer_error.j2"))
        return

    data = await state.get_data()
    user = await User.get(id=data.get("user_id"))
    await user.update(balance=user.balance + float(message.text))
    await send_message(render_template("user_balance_issue_alert.j2"), user_id=user.id)
    await send_message(render_template("balance_issued.j2"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Accounting.SetMishaBalance.amount, is_admin=True)
async def handle_set_misha_balance_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await send_message(render_template("integer_error.j2"))
        return

    data = await state.get_data()
    user = await User.get(id=data.get("user_id"))
    await user.update(misha_balance=float(message.text))
    await send_message(render_template("admin/misha_balance_set.j2"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Other.CreateOperation.amount, is_admin=True)
async def handle_create_operation_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("invalid_integer.j2"))
        return

    await send_message(render_template("create_operation/reason.j2"))
    await state.update_data(amount=float(message.text))
    await state.set_state(States.Admin.Other.CreateOperation.reason)


@dp.message_handler(state=States.Admin.Accounting.SetUserSalary.amount, is_admin=True)
async def handle_set_user_salary_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("invalid_integer.j2"))
        return

    data = await state.get_data()
    user_id = data.get("user_id")
    amount = float(message.text)
    user = await User.get(id=user_id)
    if data.get("partner") == enums.SalaryPartner.DEFAULT.value:
        salary = await Salary.get(user=user_id)
        partner_name = None
    else:
        salary = await Bet20Salary.get(user=user_id)
        partner_name = "Бет 2.0"
    await salary.update(amount=amount, last_debiting_at=datetime.datetime.now())
    await send_message(
        render_template(
            "salary_set_alert.j2",
            context={
                "amount": amount - salary.amount,
                "currency": await user.get_currency(),
                "partner_name": partner_name,
            },
        ),
        user_id=user_id,
    )
    await send_message(render_template("admin/salary_set.j2"))
    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Other.CreateOperation.reason, is_admin=True)
async def handle_create_operation_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount", 0)
    balance_type = data.get("balance_type", "")

    user = await User.get(id=data.get("user_id", 0))

    # create operation
    await create_operation(user.id, amount, message.text)
    # update user balance
    await user.update(balance=user.balance + amount)
    if balance_type == "misha":
        await user.update(misha_balance=user.misha_balance + amount)

    await send_message(render_template("create_operation/created.j2"))
    await send_message(
        render_template(
            "admin/created_operation.j2",
            context={"amount": amount, "currency": await user.get_currency()},
        ),
        user_id=user.id,
    )

    await state.reset_state(with_data=True)


@dp.message_handler(state=States.Admin.Other.Operations.date, is_admin=True)
async def handle_operations_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return
    operations = await get_operations_by_interval(interval.start, interval.end)
    if len(operations) == 0:
        await send_message(render_template("admin/no_operations.j2"))
        await state.reset_state(with_data=True)
        return

    for o in operations:
        user = await User.get(id=o.user)
        await send_message(
            render_template(
                "admin/operation.j2",
                context={"operation": o, "username": user.username},
            ),
        )
    await state.reset_state(with_data=True)
