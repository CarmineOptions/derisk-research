from aiogram import Router, types, Bot, F
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from database.models import NotificationData
from .utils import kb

menu_router = Router()


@menu_router.callback_query(F.data == "go_menu")
async def menu(callback: types.CallbackQuery, db: Session, bot: Bot):
    await callback.message.edit_text("Menu:", reply_markup=kb.menu())


@menu_router.callback_query(F.data.startswith("notification_delete_confirm_"))
async def delete_notification_confirm(callback: types.CallbackQuery, db: Session):
    # get ident
    ident = callback.data.removeprefix("notification_delete_confirm_")
    # delete notifi
    stmp = delete(NotificationData).where(NotificationData.id == ident)
    db.execute(stmp)
    db.commit()
    # answer
    await callback.message.edit_text("Notification deleted.", reply_markup=kb.menu())
    return callback.answer("Deleted notification.")


@menu_router.callback_query(F.data.startswith("notification_delete_"))
async def delete_notification(callback: types.CallbackQuery):
    # get confirm
    ident = callback.data.removeprefix("notification_delete_")
    await callback.message.edit_reply_markup(
        reply_markup=kb.confirm_delete_subscribe(ident)
    )
    return callback.answer()


@menu_router.callback_query(F.data.startswith("notification_adjust_"))
async def delete_notification(callback: types.CallbackQuery):
    # not implemented
    ident = callback.data.removeprefix("notification_adjust_")
    return callback.answer("Sorry, not ready yet. Stay tuned!")


@menu_router.callback_query(F.data == "show_notifications")
@menu_router.callback_query(F.data.startswith("notifications_"))
async def show_notifications(callback: types.CallbackQuery, db: Session):
    # get curent page
    page = 0
    if callback.data.startswith("notifications_"):
        page = int(callback.data.removeprefix("notifications_"))
    # get current page
    stmp = (
        select(NotificationData)
        .where(NotificationData.telegram_id == str(callback.from_user.id))
        .offset(page)
        .limit(1)
    )
    obj = db.scalar(stmp)
    # answer callback (from paginate)
    if not obj and callback.data.startswith("notifications_"):
        return callback.answer("Not more notifications", show_alert=True)
    # answer callback (from menu)
    if not obj:
        return callback.answer("You have no notifications", show_alert=True)
    # answer callback
    await callback.answer()
    # sand page
    await callback.message.edit_text(
        f"Wallet ID: {obj.wallet_id}\n"
        f"Health Ratio Level: {obj.health_ratio_level}\n"
        f"Protocol: {obj.protocol_id.name}",
        reply_markup=kb.pagination_notifications(obj.id, page),
    )


@menu_router.callback_query(F.data == "all_unsubscribe_confirm")
async def all_unsubscribe_confirm(callback: types.CallbackQuery, db: Session):
    # delete All notifications
    stmp = delete(NotificationData).where(
        NotificationData.telegram_id == str(callback.from_user.id)
    )
    db.execute(stmp)
    db.commit()
    # answer
    await callback.message.edit_text(
        "You are unsubscribed from all notifications.", reply_markup=kb.menu()
    )
    return callback.answer()


@menu_router.callback_query(F.data == "all_unsubscribe")
async def all_unsubscribe(callback: types.CallbackQuery):
    await callback.message.answer(
        "Are you sure you want to unsubscribe from all notifications?",
        reply_markup=kb.confirm_all_unsubscribe(),
    )
    return callback.answer()
