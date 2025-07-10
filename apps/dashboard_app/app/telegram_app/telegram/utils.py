import asyncio
from asyncio.queues import Queue, QueueFull
from contextlib import suppress
from uuid import UUID

from aiogram import exceptions
from aiogram.utils.deep_linking import create_deep_link
from shared.db import DBConnectorAsync
from app.models.watcher import NotificationData, TelegramLog

from .bot import bot

DEFAULT_MESSAGE_TEMPLATE = (
    "Warning. Your health ratio is too low for wallet_id {wallet_id}"
)


async def get_subscription_link(ident: UUID) -> str:
    """
    Generate a subscription link for a given identifier.

    :param ident: The unique identifier for the subscription (from NotificationData.id).
    :return: The generated subscription link, e.g., "https://t.me/TestBot?start=DARAAD".
    """
    me = await bot.me()
    return create_deep_link(
        username=me.username, link_type="start", payload=str(ident), encode=True
    )


class TelegramNotifications:
    """
    Class for sending Telegram notifications.

    Example:
         from database.crud import DBConnector

         telegram_notifications = TelegramNotifications(db_connector=DBConnector())

         scheduler.add_job(telegram_notifications, "interval", seconds=0.05)
         # or
         asyncio.run(telegram_notifications(is_infinity=True))

    Minimal interval 0.05 seconds, 20 messages per second (Limit: 30 messages per second)
    """

    __queue_to_send = Queue()

    @classmethod
    async def send_notification(cls, notification_id: UUID) -> None:
        """
        Add a Telegram ID to the queue for sending a notification.

        :param notification_id: Unique identifier of the NotificationData.id, which will be added to the queue for sending via Telegram.
        """
        await cls.__queue_to_send.put(notification_id)

    async def log_send(self, notification_id: UUID, text: str, is_succesfully: bool):
        """
        Logs the sending status of a message.

        :param notification_id: The UUID identifying the notification data.
        :param text: The message text that was sent.
        :param is_succesfully: A boolean indicating whether the message was sent successfully or not.
        """
        self.db_connector.write_to_db(
            TelegramLog(
                notification_data_id=notification_id,
                is_succesfully=is_succesfully,
                message=text,
            )
        )

    def __init__(
        self, db_connector: DBConnectorAsync, text: str = DEFAULT_MESSAGE_TEMPLATE
    ) -> None:
        """
        Initialize the TelegramNotifier instance.

        :param db_connector: Instance of DBConnector to handle database operations.
        :param text: The text content of the notification (which will be formatted when sent).
        """
        self.db_connector = db_connector
        self.text = text

    async def __call__(
        self, is_infinity: bool = False, sleep_time: float = 0.05
    ) -> None:
        """
        Process the queue and send notifications.

        This method processes the queue of Notifiication ID and sends notifications to each user.

        :param is_infinity: A boolean indicating whether the processing loop should continue indefinitely.
                    If set to True, the method will continuously process notifications.
                    Defaults to False.
        :param sleep_time: The time interval (in seconds) to wait between processing notifications.
                   This parameter is effective only when is_infinity is set to True.
                   Defaults to 0.05 seconds.
        """
        while notification_id := await self.__queue_to_send.get():
            # Retrieve notification data from the database based on its ID
            notification = self.db_connector.get_object(
                NotificationData, notification_id
            )
            if notification is None:
                continue  # skip is not valid notification_id
            is_succesfully = False
            # create text message
            text = self.text.format(wallet_id=notification.wallet_id)

            try:
                # Check if the notification has a Telegram ID and send the message
                if notification.telegram_id:
                    await bot.send_message(
                        chat_id=notification.telegram_id,
                        text=text,
                    )
                    is_succesfully = True
            except exceptions.TelegramRetryAfter as e:
                # If Telegram returns a RetryAfter exception, wait for the specified time and then retry
                await asyncio.sleep(e.retry_after)
                # Ignore QueueFull exception to prevent it from being raised when the queue is explicitly limited
                with suppress(QueueFull):
                    self.__queue_to_send.put_nowait(notification_id)
            except exceptions.TelegramAPIError:
                pass  # skip errors

            finally:
                # Log the sending status of the message
                await self.log_send(notification_id, text, is_succesfully)

            # If the loop is not set to infinity, break out after processing one notification
            if not is_infinity:
                break
            await asyncio.sleep(sleep_time)
