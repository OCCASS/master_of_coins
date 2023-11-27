from aiogram import types
from aiogram.dispatcher import FSMContext

from src.states import States
from src.loader import dp
from src.data import settings
from src.utils.send import send_message, send_message_to_admins, send_confirm_report
from src.utils.parse import parse_date_interval
from src.utils.validate import is_float
from src.services.templates import render_template
from src.services.database.api import (
    get_user_reports_by_interval,
    get_partners,
    create_operation,
)
from src.services.database.models import User, Partner, Currency
from src.keyboards.inline import get_select_partner_keyboard


@dp.message_handler(state=States.UserReports.date)
async def handle_user_reports_date(message: types.Message, state: FSMContext):
    interval = parse_date_interval(message.text)
    if interval is None:
        await send_message(render_template("invalid_interval.j2"))
        return
    reports = await get_user_reports_by_interval(
        message.from_user.id, interval.start, interval.end
    )
    user = await User.get(id=message.from_user.id)
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


@dp.message_handler(
    state=States.CreateReport.photo, content_types=[types.ContentType.PHOTO]
)
async def handle_create_report_photo(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    user = await User.get(id=message.from_user.id)
    currency = await user.get_currency()
    await send_message(
        render_template("create_report/amount.j2", context={"currency": currency})
    )
    await state.update_data(photo=photo, currency=currency.id)
    await state.set_state(States.CreateReport.amount)


@dp.message_handler(state=States.CreateReport.amount)
async def handle_create_report_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("invalid_integer.j2"))
        return

    data = await state.get_data()
    currency = await Currency.get(id=data.get("currency"))
    await send_message(
        render_template(
            "create_report/refund_amount.j2",
            context={"currency": currency},
        ),
    )
    await state.update_data(amount=float(message.text))
    await state.set_state(States.CreateReport.refund_amount)


@dp.message_handler(state=States.CreateReport.refund_amount)
async def handle_create_report_refund_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("invalid_integer.j2"))
        return

    partners = await get_partners()
    await send_message(
        render_template("create_report/partner.j2"),
        reply_markup=get_select_partner_keyboard(partners),
    )
    await state.update_data(refund_amount=float(message.text))
    await state.set_state(States.CreateReport.partner)


@dp.message_handler(state=States.CreateReport.salary_percent)
async def handle_create_report_salary_percent(
    message: types.Message, state: FSMContext
):
    if not message.text.isdigit():
        await send_message(render_template("invalid_integer.j2"))
        return

    if not (
        settings.MIN_SALARY_PERCENT <= int(message.text) <= settings.MAX_SALARY_PERCENT
    ):
        await send_message(render_template("create_report/invalid_salary.j2"))
        return

    data = await state.get_data()
    partner = await Partner.get(id=data.get("partner"))
    currency = await Currency.get(id=data.get("currency"))
    await send_confirm_report(
        data.get("amount", 0),
        data.get("refund_amount", 0),
        int(message.text),
        data.get("photo", ""),
        partner,
        currency,
        data.get("erroneous", False),
    )
    await state.update_data(salary_percent=int(message.text))
    await state.set_state(States.CreateReport.confirm)


@dp.message_handler(state=States.CreateOperation.amount)
async def handle_create_operation_amount(message: types.Message, state: FSMContext):
    if not is_float(message.text):
        await send_message(render_template("invalid_integer.j2"))
        return

    await send_message(render_template("create_operation/reason.j2"))
    await state.update_data(amount=float(message.text))
    await state.set_state(States.CreateOperation.reason)


@dp.message_handler(state=States.CreateOperation.reason)
async def handle_create_operation_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount", 0)

    user = await User.get(id=message.from_user.id)
    currency = await user.get_currency()

    # create operation
    operation = await create_operation(
        message.from_user.id, currency.convert_to_eur(amount), message.text
    )
    # update user balance
    await user.update(balance=user.balance + amount)
    # notify admins
    await send_message_to_admins(
        render_template(
            "create_operation/admin_alert.j2",
            context={"operation": operation, "username": message.from_user.username},
        )
    )

    await send_message(render_template("create_report/created.j2"))
    await state.reset_state(with_data=True)
