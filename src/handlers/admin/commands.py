from aiogram import types
from aiogram.dispatcher import FSMContext
from src.loader import dp
from src.utils.send import send_message
from src.services.forms.admin import start_form, balances_form
from src.services.templates import render_template


@dp.message_handler(commands=["start"], state="*", is_admin=True)
async def handle_start(message: types.Message, state: FSMContext):
    await send_message(
        render_template(
            "greeting.j2", context={"username": message.from_user.username}
        ),
        reply_markup=start_form.get_inline_keyboard(),
    )
    await state.reset_state(with_data=True)


@dp.message_handler(commands=["balance"], state="*", is_admin=True)
async def handle_balance(message: types.Message, state: FSMContext):
    await send_message(
        render_template(
            "greeting.j2", context={"username": message.from_user.username}
        ),
        reply_markup=balances_form.get_inline_keyboard(),
    )
