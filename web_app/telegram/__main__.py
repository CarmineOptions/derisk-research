import asyncio
import logging

from aiogram.types import BotCommand, BotCommandScopeDefault

from . import dp, bot
from .crud import get_async_sessionmaker, TelegramCrud
from .middleware import DatabaseMiddleware
from .notifications import TelegramNotifications


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
    # create tasks
    polling = dp.start_polling(bot)
    notify = TelegramNotifications(TelegramCrud(async_sessionmaker))
    # start tasks
    await asyncio.gather(polling, notify)



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot_start_polling())
