from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject, Command

from database.models import NotificationData
from telegram.crud import TelegramCrud
from .utils import kb

cmd_router = Router()


@cmd_router.message(Command("menu"))
async def menu(message: types.Message):
    """
    This function is triggered when the user sends the "/menu" command to the bot.
    It sends the user a message "Menu:" along with a reply markup containing a menu with buttons.
    """
    await message.answer("Menu:", reply_markup=kb.menu())


@cmd_router.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def start(message: types.Message, crud: TelegramCrud, command: CommandObject):
    """
    Register Telegram ID in the database.
    """
    await crud.update_values(NotificationData, command.args, telegram_id=message.from_user.id)

    await message.answer(
        "You are subscribed to notifications.", reply_markup=kb.go_menu()
    )
