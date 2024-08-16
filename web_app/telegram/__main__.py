import asyncio
import logging

from aiogram.types import BotCommand, BotCommandScopeDefault

from . import dp, bot
from .crud import get_async_sessionmaker
from .middleware import DatabaseMiddleware


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def bot_start_polling():
    """
    Start the bot polling loop
    (added database middleware and bot commands if is outside Flask Api server)
    """
    logger.info("Starting bot polling")
    await bot.set_my_commands(
        [BotCommand(command="menu", description="Show bot menu")],
        scope=BotCommandScopeDefault(),
    )

    async_sessionmaker = get_async_sessionmaker()
    dp.update.middleware(DatabaseMiddleware(async_sessionmaker))
    logger.info("Database middleware added")
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot_start_polling())
