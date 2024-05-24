from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def go_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Go to menu", callback_data="go_menu")]
        ]
    )


def confirm_delete_subscribe(uuid: UUID):
    markup = InlineKeyboardBuilder()
    for _ in range(4):
        markup.add(InlineKeyboardButton(text="Menu", callback_data="go_menu"))
    markup.add(
        InlineKeyboardButton(
            text="Delete", callback_data=f"notification_delete_confirm_{uuid}"
        )
    )
    markup.adjust(1, repeat=True)
    return markup.as_markup()


def confirm_all_unsubscribe():
    markup = InlineKeyboardBuilder()
    for _ in range(4):
        markup.add(InlineKeyboardButton(text="Menu", callback_data="go_menu"))
    markup.add(
        InlineKeyboardButton(
            text="Unsubscribe all", callback_data="all_unsubscribe_confirm"
        )
    )
    markup.adjust(1, repeat=True)
    return markup.as_markup()


def menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Shows notifications", callback_data="show_notifications"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Unsubscribe all", callback_data="all_unsubscribe"
                )
            ],
        ]
    )


def pagination_notifications(curent_uuid: UUID, page: int):
    markup = InlineKeyboardBuilder()
    if page > 0:
        markup.button(text="<", callback_data=f"notifications_{page - 1}")
    markup.button(text="Delete", callback_data=f"notification_delete_{curent_uuid}")
    markup.button(text=">", callback_data=f"notifications_{page + 1}")
    markup.button(text="Adjust", callback_data=f"notification_adjust_{curent_uuid}")
    markup.adjust(3, 1)
    if page == 0:
        markup.adjust(2, 1)
    return markup.as_markup()
