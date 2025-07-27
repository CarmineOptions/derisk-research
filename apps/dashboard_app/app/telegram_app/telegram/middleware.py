from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from dashboard_app.app.telegram_app.telegram.crud import TelegramCrud


class DatabaseMiddleware(BaseMiddleware):
    """Middleware for managing database sessions."""

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Execute middleware, add telegraam database crud to context using `crud` key.

        :param handler: Handler or next middeleware.
        :param event: Incoming Telegram event.
        :param data: Contextual data. Will be mapped to handler arguments

        :return: Result of handling the event.
        """
        data["crud"] = TelegramCrud(self.sessionmaker)
        try:
            return await handler(event, data)
        finally:
            del data["crud"]
