from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.contrib.fsm_storage.files import JSONStorage

from src.data import settings
from src.logger import init_logger
from src.middlewares.is_active import IsActiveMiddleware
from src.utils.filters.is_admin import IsAdmin

init_logger()

bot = Bot(token=settings.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=JSONStorage("states.json"))

# Setup throttling middleware
# dp.middleware.setup(ThrottlingMiddleware())
dp.middleware.setup(IsActiveMiddleware())

# Setup admin filter
dp.filters_factory.bind(IsAdmin)
