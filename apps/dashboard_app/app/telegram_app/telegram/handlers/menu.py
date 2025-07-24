from aiogram import F, Router, types
from dashboard_app.app.models.watcher import NotificationData
from dashboard_app.app.crud import TelegramCrud

from handlers.utils import kb

menu_router = Router()


@menu_router.callback_query(F.data == "go_menu")
async def menu(callback: types.CallbackQuery):
    """
    This function is called when the user clicks the "go_menu" button in Telegram.
    It sends the user a message "Menu:" and displays a menu with buttons.
    """
    await callback.message.edit_text("Menu:", reply_markup=kb.menu())


@menu_router.callback_query(F.data.startswith("notification_delete_confirm_"))
async def delete_notification_confirm(
    callback: types.CallbackQuery, crud: TelegramCrud
):
    """
    This function is called when the user confirms the deletion of a notification.
    It deletes the notification from the database and sends the user a message about successful deletion.
    """
    # get the notification identifier
    ident = callback.data.removeprefix("notification_delete_confirm_")
    # delete the notification
    await crud.delete_object(NotificationData, ident)
    # send a message about successful deletion
    await callback.message.edit_text("Notification deleted.", reply_markup=kb.menu())
    return callback.answer("Deleted notification.")


@menu_router.callback_query(F.data.startswith("notification_delete_"))
async def delete_notification(callback: types.CallbackQuery):
    """
    This function is called when the user wants to delete a notification.
    It prompts the user to confirm the deletion by displaying a confirmation button.
    """
    # get the notification identifier
    ident = callback.data.removeprefix("notification_delete_")
    await callback.message.edit_text(
        "Are you sure you want to delete this notification? \n\n"
        + callback.message.text,
        reply_markup=kb.confirm_delete_subscribe(ident),
    )
    return callback.answer()


@menu_router.callback_query(F.data == "show_notifications")
@menu_router.callback_query(F.data.startswith("notifications_"))
async def show_notifications(callback: types.CallbackQuery, crud: TelegramCrud):
    """
    This function is called when the user wants to view their notifications.
    It retrieves the notifications from the database and displays them to the user.
    It also handles pagination if there are multiple notifications.
    """
    # get the current page
    page = 0
    if callback.data.startswith("notifications_"):
        page = int(callback.data.removeprefix("notifications_"))
    # get the current page of notifications
    obj = await crud.get_objects_by_filter(
        NotificationData, page, 1, telegram_id=str(callback.from_user.id)
    )
    # handle callback answer (from pagination)
    if not obj and callback.data.startswith("notifications_"):
        return callback.answer("Not more notifications", show_alert=True)
    # handle callback answer (from menu)
    if not obj:
        return callback.answer("You have no notifications", show_alert=True)
    # handle callback answer
    await callback.answer()
    # send the notification page
    await callback.message.edit_text(
        f"Wallet ID: {obj.wallet_id}\n"
        f"Health Ratio Level: {obj.health_ratio_level}\n"
        f"Protocol: {obj.protocol_id.name}",
        reply_markup=kb.pagination_notifications(obj.id, page),
    )


@menu_router.callback_query(F.data == "all_unsubscribe_confirm")
async def all_unsubscribe_confirm(callback: types.CallbackQuery, crud: TelegramCrud):
    # delete all notifications for the user
    await crud.delete_objects_by_filter(
        NotificationData, telegram_id=str(callback.from_user.id)
    )
    # send a confirmation message
    await callback.message.edit_text(
        "You are unsubscribed from all notifications.", reply_markup=kb.menu()
    )
    return callback.answer()


@menu_router.callback_query(F.data == "all_unsubscribe")
async def all_unsubscribe(callback: types.CallbackQuery):
    """
    This function is called when the user wants to unsubscribe from all notifications.
    It prompts the user to confirm the action by displaying a confirmation button.
    """
    await callback.message.edit_text(
        "Are you sure you want to unsubscribe from all notifications?",
        reply_markup=kb.confirm_all_unsubscribe(),
    )
    return callback.answer()
