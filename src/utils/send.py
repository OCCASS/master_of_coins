from typing import Optional

from aiogram import types

from src.loader import bot
from src.services.database.api import get_admin_users
from src.services.database.models import Currency, Partner
from src.services.templates import render_template
from src.services.forms import confirm_form
from src.keyboards.inline.callbacks import confirm_report


async def get_chat_id() -> int:
    """This function used to get current chat id"""
    chat = types.Chat.get_current()
    if chat is None:
        chat = types.User.get_current()

    return chat.id


async def send_message(
    message_text: str,
    reply_markup: types.ReplyKeyboardMarkup | types.InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
    user_id: Optional[int] = None,
    photo: Optional[str | types.InputFile] = None,
    reply_to_message_id: Optional[int] = None,
) -> types.Message:
    """
    This function used to send message to user, with default keyboard if keyboard not given in arg
    if user is admin method send message using admin keyboard

    :param message_text: message text, required parameter
    :param reply_markup: keyboard sent with message
    :param parse_mode: message parse mode
    :param user_id: to message user id
    :param photo: photo sent with message
    :param reply_to_message_id: reply to message id
    :return: sent message
    """

    if not user_id:
        user_id = await get_chat_id()

    if reply_markup is None:
        reply_markup = types.ReplyKeyboardRemove()

    if photo:
        return await bot.send_photo(
            user_id,
            photo=photo,
            caption=message_text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
        )

    return await bot.send_message(
        user_id,
        message_text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_message_id,
    )


async def send_message_to_admins(
    message_text: str,
    reply_markup: Optional[
        types.ReplyKeyboardMarkup
        | types.InlineKeyboardMarkup
        | types.ReplyKeyboardRemove
    ] = None,
    parse_mode: str = "HTML",
    photo: Optional[str | types.InputFile] = None,
    reply_to_message_id: Optional[int] = None,
) -> None:
    admins = await get_admin_users()
    for admin in admins:
        await send_message(
            message_text=message_text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            photo=photo,
            reply_to_message_id=reply_to_message_id,
            user_id=admin.id,
        )


async def send_confirm_report(
    amount: float,
    refund_amount: float,
    salary_percent: int,
    photo: str,
    partner: Partner,
    currency: Currency,
    erroneous: bool,
):
    await send_message(
        render_template(
            "create_report/confirm.j2",
            context={
                "amount": amount,
                "refund_amount": refund_amount,
                "salary_percent": salary_percent,
                "partner": partner,
                "currency": currency,
                "erroneous": erroneous,
            },
        ),
        photo=photo,
        reply_markup=confirm_form.get_inline_keyboard(
            row_width=2, callback_data=confirm_report
        ),
    )
