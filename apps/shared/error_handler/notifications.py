import asyncio
import logging
from uuid import uuid4

from aiogram import Bot, Dispatcher

from .config import ERROR_CHAT_ID, TELEGRAM_TOKEN
from .values import Message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

dispatcher = Dispatcher()


from uuid import uuid4
from typing import Optional


class Message:
    def __init__(self, text: str, is_sent: bool):
        self.text = text
        self.is_sent = is_sent


class ErrorHandlerBot:
    SESSION_ID = str(uuid4())
    SESSION_MESSAGES = {SESSION_ID: []}

    def __init__(self, token: Optional[str]) -> None:
        """
        Initialize the error handler bot.
        :param token: Optional[str]
        """
        if not token:
            self.bot = None
        else:
            self.bot = Bot(token=token)

    def add_message(self, message):
        """Add message to session, enforce type"""
        if not isinstance(message, Message):
            raise TypeError("Only Message instances are allowed")
        self.SESSION_MESSAGES[self.SESSION_ID].append(message)

    def _get_unique_message(self, new_message: str) -> Optional[str]:
        """
        Check if the message is unique.
        :param new_message: str
        :return: str | None
        """
        messages = self.SESSION_MESSAGES[self.SESSION_ID]
        not_sent_messages = list(filter(lambda message: not message.is_sent, messages))

        for message in not_sent_messages:
            if message.text != new_message:
                return new_message

    async def send_message(self, message: str) -> None:
        """
        Send a message to a chat.
        This method checks if the session has any messages. If not, it sends the message to the error chat
        and closes the bot. If the session has messages, it checks if the message is unique. If it is,
        it sends the message to the error chat and closes the bot. If the message is not unique, it adds
        the message to the session messages but does not send it.
        :param message: str
        :return: None
        """
        if not self.bot:
            logger.error(f"Telegram bot token debug mode: {message}")
            return

        if not self.SESSION_MESSAGES[self.SESSION_ID]:
            await self.bot.send_message(chat_id=ERROR_CHAT_ID, text=message)
            self.add_message(Message(text=message, is_sent=True))
            await self.bot.close()

        elif self._get_unique_message(message):
            await self.bot.send_message(chat_id=ERROR_CHAT_ID, text=message)
            self.add_message(Message(text=message, is_sent=True))
            await self.bot.close()

        else:
            self.add_message(Message(text=message, is_sent=False))


BOT = ErrorHandlerBot(TELEGRAM_TOKEN)

if __name__ == "__main__":
    asyncio.run(dispatcher.start_polling(BOT.bot))
