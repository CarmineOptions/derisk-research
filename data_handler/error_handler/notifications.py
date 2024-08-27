import logging
from uuid import uuid4

import asyncio
from aiogram import Bot, Dispatcher
from .values import Message
from .config import TELEGRAM_TOKEN, ERROR_CHAT_ID

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

dispatcher = Dispatcher()


class TelegramBot:
    SESSION_ID = str(uuid4())
    SESSION_MESSAGES = {SESSION_ID: []}

    def __init__(self, token):
        self.bot = Bot(token=token)

    def _get_unique_message(self, new_message: str) -> str | None:
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
        :param message: str
        :return: None
        """

        if not self.SESSION_MESSAGES[self.SESSION_ID]:
            await self.bot.send_message(chat_id=ERROR_CHAT_ID, text=message)
            self.SESSION_MESSAGES[self.SESSION_ID].append(Message(text=message, is_sent=True))
            await self.bot.close()

        elif self._get_unique_message(message):
            await self.bot.send_message(chat_id=ERROR_CHAT_ID, text=message)
            self.SESSION_MESSAGES[self.SESSION_ID].append(Message(text=message, is_sent=True))
            await self.bot.close()

        else:
            self.SESSION_MESSAGES[self.SESSION_ID].append(Message(text=message, is_sent=False))


my_bot = TelegramBot(TELEGRAM_TOKEN)

if __name__ == '__main__':
    asyncio.run(dispatcher.start_polling(my_bot.bot))