import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

from .crud import get_async_sessionmaker
from .middleware import DatabaseMiddleware

from .config import TELEGRAM_TOKEN, X_TELEGRAM_BOT_API_SECRET_TOKEN, BASE_URL
from .handlers import index_router

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
dp.include_router(index_router)


async def on_startup(bot: Bot) -> None:  
    # TODO fix url if needed on prod.
    await bot.set_webhook(
        f"{BASE_URL}/api/telegram/webhook", secret_token=X_TELEGRAM_BOT_API_SECRET_TOKEN
    )


async def bot_start_polling():
    """
    Start the bot polling loop
    (added database middleware and bot commands if is outside Flask Api server)
    """
    await bot.set_my_commands(
        [BotCommand(command="menu", description="Show bot menu")],
        scope=BotCommandScopeDefault(),
    )

    async_sessionmaker = get_async_sessionmaker()
    dp.update.middleware(DatabaseMiddleware(async_sessionmaker))

    await dp.start_polling(bot)


def start_telegram_bot():
    if bot is not None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot_start_polling())
