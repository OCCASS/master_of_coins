from typing import Sequence

from aiogram import types

from src.loader import bot
from src.services.database.models import Partner, User, Currency
from .callbacks import select_partner, select_user, select_currency


def get_select_partner_keyboard(
        partners: Sequence[Partner], all_partner_button: bool = False
) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    if all_partner_button:
        keyboard.add(
            types.InlineKeyboardButton("Все", callback_data=select_partner.new(id=-1))
        )
    for p in partners:
        keyboard.add(
            types.InlineKeyboardButton(
                p.name, callback_data=select_partner.new(id=p.id)
            )
        )
    return keyboard


async def get_select_users_keyboard(
        users: Sequence[User],
) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    for u in users:
        keyboard.add(
            types.InlineKeyboardButton(
                u.username, callback_data=select_user.new(id=u.id)
            )
        )
    return keyboard


async def get_select_currency_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    for c in await Currency.all():
        keyboard.add(
            types.InlineKeyboardButton(
                f"{c.name} ({c.symbol})", callback_data=select_currency.new(id=c.id)
            )
        )
    return keyboard
