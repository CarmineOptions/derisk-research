from aiogram import Bot, Dispatcher

from .config import TELEGRAM_TOKEN
from .handlers import index_router

if TELEGRAM_TOKEN:
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()

    dp.include_router(index_router)
else:
    bot = None
    dp = None
