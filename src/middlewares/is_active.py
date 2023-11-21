from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from src.services.database.models import User


class IsActiveMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        user = await User.get(id=message.from_user.id)

        if not user:
            return

        if not user.active:
            raise CancelHandler()
