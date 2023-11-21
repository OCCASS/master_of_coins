from aiogram import types
from aiogram.dispatcher import FSMContext

from src.keyboards.inline.callbacks import accept_new_user
from src.loader import dp
from src.services.database.models import User
from src.services.forms import start_form, balance_form
from src.services.forms.admin import accept_new_user_form
from src.services.templates import render_template
from src.utils.send import send_message, send_message_to_admins


@dp.message_handler(commands=["start"], state="*")
async def start_command(message: types.Message, state: FSMContext):
    user = await User.get(id=message.from_user.id)
    if user is None:
        await send_message_to_admins(
            render_template(
                "admin/membership_request.j2", context={"username": message.from_user.username}
            ),
            reply_markup=accept_new_user_form.get_inline_keyboard(
                row_width=2,
                callback_data=accept_new_user,
                callback_data_args={"user_id": message.from_user.id},
            ),
        )
        await send_message(render_template("membership_request_sent.j2"))
        return

    await send_message(
        render_template("greeting.j2", context={"username": message.from_user.username}),
        reply_markup=start_form.get_inline_keyboard(rows_template=(1, 2)),
    )
    await state.reset_state(with_data=True)


@dp.message_handler(commands=["balance"], state="*")
async def balance_command(message: types.Message, state: FSMContext):
    await send_message(
        render_template("greeting.j2", context={"username": message.from_user.username}),
        reply_markup=balance_form.get_inline_keyboard(),
    )
