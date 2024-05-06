from typing import Callable, Dict, Any, Awaitable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.orm import sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware for managing database sessions."""

    def __init__(self, session_pool: sessionmaker):
        """
        :param session_pool: SQLAlchemy session pool.
        """
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Execute middleware, add database session to context using `db` key.

        :param handler: Handler or next middeleware.
        :param event: Incoming Telegram event.
        :param data: Contextual data. Will be mapped to handler arguments

        :return: Result of handling the event.
        """
        data["db"] = self.session_pool()
        try:
            return await handler(event, data)
        finally:
            data["db"].close()
            del data["db"]
