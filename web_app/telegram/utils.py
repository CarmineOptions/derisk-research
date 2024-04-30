from asyncio.queues import Queue
from uuid import UUID

from aiogram.utils.deep_linking import create_deep_link

from .bot import bot


async def get_subscription_link(ident: UUID):
    me = await bot.me()
    return create_deep_link(username=me.username, link_type="start", payload=str(ident), encode=True)


class TelegramNotifications:
    __queue_to_send = Queue()

    @classmethod
    async def send_notification(cls, telegram_id: int):
        await cls.__queue_to_send.put(telegram_id)

    async def __call__(self):
        while ident := await self.__queue_to_send.get():
            await bot.send_message(chat_id=ident, text="Test message")
