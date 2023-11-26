import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext

from src.keyboards.inline import (
    get_select_users_keyboard,
    get_select_partner_keyboard,
    get_select_currency_keyboard,
)
from src.data import enums, settings
from src.services.forms.admin import manage_partners_form, manage_salary_form
from src.loader import dp, bot
from src.states import States
from src.utils.send import send_message
from src.services.templates import render_template
from src.keyboards.inline.callbacks import (
    accept_new_user,
    select_user,
    select_partner,
    select_currency,
    delete_report,
    confirm_deletion,
)
from src.services.calc import (
    get_common_balance,
    get_common_misha_balance,
    get_common_salary,
    get_common_total_charity,
    get_common_charity,
    get_common_bet20_salary,
)
from src.services.forms.admin import (
    accept_new_user_form,
    start_form,
    accounting_form,
    balances_form,
    other_form,
    reports_form,
    manage_charity_form,
    confirm_deletion_form,
    delete_report_form,
    salary_partner_form,
    remove_charity_form,
    current_month_form,
    balance_type_form,
)
from src.services.database.api import (
    create_user,
    create_salary,
    create_bet20_salary,
    create_charity,
    get_users,
    get_partners,
    get_not_admin_users,
    get_admin_users,
    get_salaries,
    get_bet20_salaries,
    deactive_report,
    get_charities,
    get_reports_by_interval,
    get_operations_by_interval,
)
from src.services.database.models import User, Partner, Salary, Bet20Salary, Report
from src.utils.parse import get_current_month_interval


@dp.callback_query_handler(
    current_month_form.callback_data().filter(),
    state=States.Admin.Reports.Statistic.date,
    is_admin=True,
)
async def handle_reports_statistic_date_month(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    interval = get_current_month_interval()
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


@dp.callback_query_handler(
    current_month_form.callback_data().filter(),
    state=States.Admin.Other.Operations.date,
    is_admin=True,
)
async def handle_operations_date_month(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    interval = get_current_month_interval()
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


@dp.callback_query_handler(delete_report.filter(), state="*")
async def handle_delete_report(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    report_id = callback_data.get("report_id")
    await query.message.edit_reply_markup(
        confirm_deletion_form.get_inline_keyboard(
            callback_data=confirm_deletion, callback_data_args={"report_id": report_id}
        )
    )


@dp.callback_query_handler(confirm_deletion.filter(), state="*")
async def handle_confirm_deletion(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    option_id = callback_data.get("id")
    report_id = int(callback_data.get("report_id", 0))

    match option_id:
        case confirm_deletion_form.yes:
            await query.message.delete()
            report = await Report.get(id=report_id)
            user = await User.get(id=report.user)
            salary = await user.get_salary()
            salary_percent = report.salary_percent
            if report.partner == settings.BET_20_PARTNER_ID:
                salary = await user.get_bet20_salary()
                salary_fraction = settings.BET_20_SALARY_FRACTION
            else:
                salary = await user.get_salary()
                salary_fraction = salary_percent / 100
            # process report as erroneous
            if report.erroneous and report.partner != settings.BET_20_PARTNER_ID:
                salary_fraction = 0
                if report.profit() < 0:
                    # fine amount < 0, because report.profit() < 0
                    fine_amount = report.profit() * 3 * settings.DEFAULT_SALARY_FRACTION
                    await salary.update(amount=salary.amount - fine_amount)

            # update user salary
            update_amount = report.amount * salary_fraction
            await salary.update(
                amount=salary.amount - update_amount,
                total_amount=salary.total_amount - update_amount,
            )

            # update user balance to report profit
            await user.update(balance=user.balance - float(report.profit()))
            if report.partner == settings.MISHA_PARTNER_ID:
                await user.update(
                    misha_balance=user.misha_balance - float(report.profit()) * 0.5
                )
            # update charity balance
            charity = await user.get_charity()
            update_amount = report.amount * settings.CHARITY_FRACTION
            await charity.update(
                amount=charity.amount - update_amount,
                total_amount=charity.total_amount - update_amount,
            )
            await deactive_report(report_id)
        case confirm_deletion_form.no:
            await query.message.edit_reply_markup(
                delete_report_form.get_inline_keyboard(
                    callback_data=delete_report,
                    callback_data_args={"report_id": report_id},
                    row_width=2,
                )
            )

    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    manage_partners_form.callback_data().filter(),
    is_admin=True,
    state=States.Admin.Other.ManagePartners.action,
)
async def handle_manage_partners_action(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case manage_partners_form.add:
            await send_message(
                render_template("admin/partner_name.j2"),
                reply_markup=None,
            )
            await state.set_state(States.Admin.Other.ManagePartners.Add.name)
        case manage_partners_form.remove:
            keyboard = get_select_partner_keyboard(await get_partners())
            await send_message(
                render_template("admin/partner.j2"), reply_markup=keyboard
            )
            await state.set_state(States.Admin.Other.ManagePartners.Remove.partner)


@dp.callback_query_handler(
    select_partner.filter(),
    is_admin=True,
    state=States.Admin.Other.ManagePartners.Remove.partner,
)
async def handle_remove_partner_partner(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    partner_id = int(callback_data.get("id", -1))
    partner = await Partner.get(id=partner_id)
    await partner.update(active=False)
    await send_message(render_template("admin/partner_removed.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(accept_new_user.filter(), is_admin=True, state="*")
async def handle_accept_new_user_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")
    user_id = int(callback_data.get("user_id", -1))

    user = await User.get(id=user_id)

    if user:
        await send_message(render_template("admin/user_already_accepted.j2"))
        return

    match option_id:
        case accept_new_user_form.accept:
            username = (await bot.get_chat(user_id)).username
            await create_user(user_id, username)
            await create_salary(user_id)
            await create_bet20_salary(user_id)
            await create_charity(user_id)
            await send_message(
                render_template("membership_request_accepted.j2"), user_id=user_id
            )
        case accept_new_user_form.decline:
            await send_message(
                render_template("membership_request_declined.j2"), user_id=user_id
            )


@dp.callback_query_handler(
    balance_type_form.callback_data().filter(),
    state=States.Admin.Other.CreateOperation.balance_type,
    is_admin=True,
)
async def handle_create_operation_balance_type(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")
    await send_message(
        render_template("admin/amount.j2"), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(
        balance_type="default" if option_id == balance_type_form.default else "misha"
    )
    await state.set_state(States.Admin.Other.CreateOperation.amount)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.CreateOperation.user
)
async def handle_create_operations_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    await send_message(
        render_template("admin/select_balance.j2"),
        reply_markup=balance_type_form.get_inline_keyboard(),
    )
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Other.CreateOperation.balance_type)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Reports.User.user
)
async def handle_user_reports_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    await send_message(
        render_template("enter_date.j2"), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Reports.User.date)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.AddAdmin.user
)
async def handle_add_admin_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    user = await User.get(id=user_id)
    await user.update(is_admin=True)
    await send_message(render_template("admin/user_admin_success.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.RemoveAdmin.user
)
async def handle_remove_admin_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    user = await User.get(id=user_id)
    await user.update(is_admin=False)
    await send_message(render_template("admin/user_not_admin_success.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    select_user.filter(),
    is_admin=True,
    state=States.Admin.Accounting.SetMishaBalance.user,
)
async def handle_remove_admin_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    await send_message(render_template("admin/amount.j2"))
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Accounting.SetMishaBalance.amount)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.RemoveUser.user
)
async def handle_remove_user_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    user = await User.get(id=user_id)
    await user.update(active=False)
    await send_message(render_template("admin/user_removed.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.IssueBalance.user
)
async def handle_issue_balance_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    await send_message(
        render_template("admin/amount.j2"), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Other.IssueBalance.amount)


@dp.callback_query_handler(
    select_user.filter(),
    is_admin=True,
    state=States.Admin.Accounting.RemoveUserSalary.user,
)
async def handle_remove_user_salary_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    data = await state.get_data()
    if data.get("partner") == enums.SalaryPartner.DEFAULT.value:
        salary = await Salary.get(user=user_id)
        partner_name = None
    else:
        salary = await Bet20Salary.get(user=user_id)
        partner_name = "Бет 2.0"
    if salary.amount > 0:
        amount = salary.amount
        await salary.update(amount=0, last_debiting_at=datetime.datetime.now())
        user = await User.get(id=salary.user)
        await user.update(balance=user.balance - amount)
        await send_message(
            render_template(
                "salary_set_alert.j2",
                context={
                    "amount": amount,
                    "currency": await user.get_currency(),
                    "partner_name": partner_name,
                },
            ),
            user_id=user_id,
        )
        await send_message(render_template("admin/salary_removed.j2"))
    else:
        await send_message(render_template("admin/salary_is_lower_than_0.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    select_user.filter(),
    is_admin=True,
    state=States.Admin.Accounting.SetUserSalary.user,
)
async def handle_set_user_salary_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    await send_message(render_template("admin/amount.j2"))
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Accounting.SetUserSalary.amount)


@dp.callback_query_handler(
    select_user.filter(), is_admin=True, state=States.Admin.Other.SetCurrency.user
)
async def handle_set_currency_user(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    user_id = int(callback_data.get("id", 0))
    keyboard = await get_select_currency_keyboard()
    await send_message(render_template("admin/currency.j2"), reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.set_state(States.Admin.Other.SetCurrency.currency)


@dp.callback_query_handler(
    select_currency.filter(),
    is_admin=True,
    state=States.Admin.Other.SetCurrency.currency,
)
async def handle_set_currency_currency(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    data = await state.get_data()
    user = await User.get(id=data.get("user_id"))
    currency_id = int(callback_data.get("id"))
    await user.update(currency=currency_id)
    await send_message(render_template("admin/currency_set.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    select_partner.filter(), is_admin=True, state=States.Admin.Reports.Partner.partner
)
async def handle_partner_reports_partner(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    partner_id = int(callback_data.get("id", -2))
    await send_message(
        render_template("enter_date.j2"), reply_markup=types.ReplyKeyboardRemove()
    )
    await state.update_data(partner_id=partner_id)
    await state.set_state(States.Admin.Reports.Partner.date)


@dp.callback_query_handler(
    salary_partner_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_salary_patner(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    partner = enums.SalaryPartner.DEFAULT
    match option_id:
        case salary_partner_form.bet20:
            partner = enums.SalaryPartner.BET_20

    salaries_func = (
        get_salaries if partner == enums.SalaryPartner.DEFAULT else get_bet20_salaries
    )
    salaries = await salaries_func()
    data = []
    for s in salaries:
        user = await User.get(id=s.user)
        data.append({"user": user, "salary": s})
    await send_message(
        render_template("admin/user_salaries.j2", context={"data": data}),
        reply_markup=manage_salary_form.get_inline_keyboard(row_width=2),
    )
    await state.update_data(partner=partner.value)


@dp.callback_query_handler(
    remove_charity_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_remove_chairty(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()

    charities = await get_charities()
    for c in charities:
        await c.update(amount=0, last_debiting_at=datetime.datetime.now())
    await send_message(render_template("admin/charity_removed.j2"))
    await state.reset_state(with_data=True)


@dp.callback_query_handler(
    manage_charity_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_manage_charity(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case manage_charity_form.statistic:
            common_total_charity = await get_common_total_charity()
            common_charity = await get_common_charity()
            await send_message(
                render_template(
                    "admin/charity_statistic.j2",
                    context={
                        "common_total": common_total_charity,
                        "common": common_charity,
                    },
                ),
                reply_markup=remove_charity_form.get_inline_keyboard(),
            )
        case manage_charity_form.report:
            await send_message(render_template("enter_date.j2"))
            await state.set_state(States.Admin.Accounting.ChairtyReport.date)


@dp.callback_query_handler(
    manage_salary_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_manage_salary(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")
    data = await state.get_data()
    salaries_func = (
        get_salaries
        if data.get("partner") == enums.SalaryPartner.DEFAULT.value
        else get_bet20_salaries
    )
    partner_name = (
        None if data.get("partner") == enums.SalaryPartner.DEFAULT.value else "Бет 2.0"
    )

    match option_id:
        case manage_salary_form.remove_everyone:
            salaries = await salaries_func()
            for s in salaries:
                if s.amount <= 0:
                    continue
                amount = s.amount
                await s.update(amount=0, last_debiting_at=datetime.datetime.now())
                user = await User.get(id=s.user)
                await user.update(balance=user.balance - amount)
                await send_message(
                    render_template(
                        "salary_set_alert.j2",
                        context={
                            "amount": amount,
                            "partner_name": partner_name,
                            "currency": await user.get_currency(),
                        },
                    ),
                    user_id=s.user,
                )
            await send_message(render_template("admin/salary_removed.j2"))
        case manage_salary_form.remove_user:
            select_user_keyboard = await get_select_users_keyboard(await get_users())
            await send_message(
                render_template("admin/user.j2"), reply_markup=select_user_keyboard
            )
            await state.set_state(States.Admin.Accounting.RemoveUserSalary.user)
        case manage_salary_form.set_user:
            select_user_keyboard = await get_select_users_keyboard(await get_users())
            await send_message(
                render_template("admin/user.j2"), reply_markup=select_user_keyboard
            )
            await state.set_state(States.Admin.Accounting.SetUserSalary.user)


@dp.callback_query_handler(
    accounting_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_accounting_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    option_id = callback_data.get("id")

    match option_id:
        case accounting_form.set_misha_balance:
            await query.message.delete_reply_markup()
            select_user_keyboard = await get_select_users_keyboard(await get_users())
            await send_message(
                render_template("admin/user.j2"), reply_markup=select_user_keyboard
            )
            await state.set_state(States.Admin.Accounting.SetMishaBalance.user)
        case accounting_form.users_salary:
            await query.message.edit_text(
                render_template("admin/select_action.j2"),
                reply_markup=salary_partner_form.get_inline_keyboard(),
            )
        case accounting_form.charity:
            await query.message.delete_reply_markup()
            await send_message(
                render_template("admin/select_action.j2"),
                reply_markup=manage_charity_form.get_inline_keyboard(),
            )
        case accounting_form.back:
            await query.message.edit_reply_markup(start_form.get_inline_keyboard())


@dp.callback_query_handler(
    balances_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_balances_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case balances_form.common:
            users = await get_users()
            common_balance = round(await get_common_balance(), 2)
            await send_message(
                render_template(
                    "admin/common_balance.j2",
                    context={"balance": common_balance, "users": users},
                )
            )
        case balances_form.misha:
            users = await get_users()
            common_balance = round(await get_common_misha_balance(), 2)
            await send_message(
                render_template(
                    "admin/common_misha_balance.j2",
                    context={"balance": common_balance, "users": users},
                )
            )
        case balances_form.business:
            common_balance = round(await get_common_balance(), 2)
            common_misha_balance = abs(round(await get_common_misha_balance(), 2))
            common_salary = abs(round(await get_common_salary(), 2))
            common_bet20_salary = abs(round(await get_common_bet20_salary(), 2))
            total = (
                common_balance
                - common_misha_balance
                - common_salary
                - common_bet20_salary
            )
            await send_message(
                render_template(
                    "admin/business_balance.j2",
                    context={
                        "balance": common_balance,
                        "misha_balance": common_misha_balance,
                        "salary": common_salary,
                        "bet20_salary": common_bet20_salary,
                        "total": total,
                    },
                )
            )


@dp.callback_query_handler(
    reports_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_reports_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case reports_form.user_reports:
            select_user_keyboard = await get_select_users_keyboard(await get_users())
            await send_message(
                render_template("admin/user.j2"), reply_markup=select_user_keyboard
            )
            await state.set_state(States.Admin.Reports.User.user)
        case reports_form.partner_reports:
            select_partner_keyboard = get_select_partner_keyboard(
                await get_partners(), all_partner_button=True
            )
            await send_message(
                render_template("admin/partner.j2"),
                reply_markup=select_partner_keyboard,
            )
            await state.set_state(States.Admin.Reports.Partner.partner)
        case reports_form.statistic:
            await send_message(
                render_template("enter_date.j2"),
                reply_markup=current_month_form.get_inline_keyboard(),
            )
            await state.set_state(States.Admin.Reports.Statistic.date)
        case reports_form.back:
            await query.message.edit_reply_markup(start_form.get_inline_keyboard())


@dp.callback_query_handler(
    other_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_other_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await query.message.delete_reply_markup()
    option_id = callback_data.get("id")

    match option_id:
        case other_form.issue_balance:
            select_user_keyboard = await get_select_users_keyboard(await get_users())
            await send_message(
                render_template("admin/user.j2"), reply_markup=select_user_keyboard
            )
            await state.set_state(States.Admin.Other.IssueBalance.user)
        case other_form.create_operation:
            users = await get_users()
            keyboard = await get_select_users_keyboard(users)
            await send_message(render_template("admin/user.j2"), reply_markup=keyboard)
            await state.set_state(States.Admin.Other.CreateOperation.user)
        case other_form.get_operations:
            await send_message(
                render_template("enter_date.j2"),
                reply_markup=current_month_form.get_inline_keyboard(),
            )
            await state.set_state(States.Admin.Other.Operations.date)
        case other_form.add_admin:
            not_admin_users = await get_not_admin_users()
            keyboard = await get_select_users_keyboard(not_admin_users)
            await send_message(render_template("admin/user.j2"), reply_markup=keyboard)
            await state.set_state(States.Admin.Other.AddAdmin.user)
        case other_form.remove_admin:
            admin_users = await get_admin_users()
            keyboard = await get_select_users_keyboard(admin_users)
            await send_message(render_template("admin/user.j2"), reply_markup=keyboard)
            await state.set_state(States.Admin.Other.RemoveAdmin.user)
        case other_form.remove_user:
            users = await get_users()
            keyboard = await get_select_users_keyboard(users)
            await send_message(render_template("admin/user.j2"), reply_markup=keyboard)
            await state.set_state(States.Admin.Other.RemoveUser.user)
        case other_form.set_currency:
            users = await get_users()
            keyboard = await get_select_users_keyboard(users)
            await send_message(render_template("admin/user.j2"), reply_markup=keyboard)
            await state.set_state(States.Admin.Other.SetCurrency.user)
        case other_form.manage_partners:
            await send_message(
                render_template("admin/select_action.j2"),
                reply_markup=manage_partners_form.get_inline_keyboard(row_width=2),
            )
            await state.set_state(States.Admin.Other.ManagePartners.action)
        case other_form.back:
            await query.message.edit_reply_markup(start_form.get_inline_keyboard())


@dp.callback_query_handler(
    start_form.callback_data().filter(), is_admin=True, state="*"
)
async def handle_start_form(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    option_id = callback_data.get("id")

    match option_id:
        case start_form.accounting:
            await query.message.edit_reply_markup(accounting_form.get_inline_keyboard())
        case start_form.reports:
            await query.message.edit_reply_markup(reports_form.get_inline_keyboard())
        case start_form.other:
            await query.message.edit_reply_markup(other_form.get_inline_keyboard())
