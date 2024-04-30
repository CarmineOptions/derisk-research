from . import dp, bot
from .middleware import DatabaseMiddleware
import asyncio
from database.database import SessionLocal

async def main():
    dp.update.middleware(
        DatabaseMiddleware(SessionLocal)
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())