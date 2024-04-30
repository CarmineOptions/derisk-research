from typing import Callable, Dict, Any, Awaitable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.orm import sessionmaker

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool: sessionmaker):
        self.session_pool = session_pool

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        data['db'] = self.session_pool()
        try:
            await handler(event, data)
        finally:
            data['db'].close()
            del data['db']