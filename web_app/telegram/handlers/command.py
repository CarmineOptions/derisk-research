from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject, Command
from sqlalchemy import update
from sqlalchemy.orm import Session

from database.models import NotificationData
from .utils import kb

cmd_router = Router()


@cmd_router.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer("Menu:", reply_markup=kb.menu())


@cmd_router.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def start(message: types.Message, db: Session, command: CommandObject):
    """
    Register Telegram ID in the database.

    :param message: The Telegram message, typically a "/start" command.
    :param db: The database session.
    :param command: The extracted data from the CommandStart filter.
    """
    ident = command.args
    stmp = (
        update(NotificationData)
        .where(NotificationData.id == ident)
        .values(telegram_id=message.from_user.id)
    )
    db.execute(stmp)
    db.commit()
    await message.answer(
        "You are subscribed to notifications.", reply_markup=kb.go_menu()
    )
