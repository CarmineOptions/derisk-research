from aiogram import Bot, Dispatcher

from .config import TELEGRAM_TOKEN

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

from .handlers import base_router

dp.include_router(base_router)
