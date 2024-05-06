from aiogram import Bot, Dispatcher

from .config import TELEGRAM_TOKEN
from .handlers import base_router

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

dp.include_router(base_router)
