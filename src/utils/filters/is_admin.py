from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from src.services.database.models import User


class IsAdmin(BoundFilter):
    key = "is_admin"

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        chat = message.message.chat if isinstance(message, types.CallbackQuery) else message.chat
        if chat.type != types.ChatType.PRIVATE:
            return False
        user = await User.get(id=message.from_user.id)
        if user:
            return user.is_admin
        return False
