from uuid import UUID

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.values import ProtocolIDs


def go_menu():
    """
    Returns an InlineKeyboardMarkup with a single button labeled "Go to menu".
    The callback data for this button is "go_menu".
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Go to menu", callback_data="go_menu")]
        ]
    )


def confirm_delete_subscribe(uuid: UUID):
    """
    Takes a UUID object as an argument.
    Builds an InlineKeyboardMarkup with the following buttons:
    - One button labeled "No" with the callback data "go_menu".
    - One button labeled "Delete" with the callback data "notification_delete_confirm_{uuid}",
      where {uuid} is the provided UUID.
    The buttons are arranged in a specific layout using the InlineKeyboardBuilder.
    Returns the constructed InlineKeyboardMarkup.
    """
    markup = InlineKeyboardBuilder()
    markup.add(InlineKeyboardButton(text="No", callback_data="go_menu"))
    markup.add(
        InlineKeyboardButton(
            text="Yes (delete)", callback_data=f"notification_delete_confirm_{uuid}"
        )
    )
    markup.adjust(1, repeat=True)
    return markup.as_markup()


def confirm_all_unsubscribe():
    """
    Builds an InlineKeyboardMarkup with the following buttons:
    - One button labeled "No" with the callback data "go_menu".
    - One button labeled "Unsubscribe all" with the callback data "all_unsubscribe_confirm".
    The buttons are arranged in a specific layout using the InlineKeyboardBuilder.
    Returns the constructed InlineKeyboardMarkup.
    """
    markup = InlineKeyboardBuilder()
    markup.add(InlineKeyboardButton(text="No", callback_data="go_menu"))
    markup.add(
        InlineKeyboardButton(
            text="Yes(Unsubscribe all)", callback_data="all_unsubscribe_confirm"
        )
    )
    markup.adjust(1, repeat=True)
    return markup.as_markup()


def menu():
    """
    Returns an InlineKeyboardMarkup with two buttons:
    - A button labeled "Shows notifications" with the callback data "show_notifications".
    - A button labeled "Unsubscribe all" with the callback data "all_unsubscribe".
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Shows notifications", callback_data="show_notifications"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Create subscription", callback_data="create_subscription"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Unsubscribe all", callback_data="all_unsubscribe"
                )
            ],
        ]
    )


def pagination_notifications(curent_uuid: UUID, page: int):
    """
    Takes a UUID object and an integer representing the current page as arguments.
    Builds an InlineKeyboardMarkup with the following buttons:
    - A button labeled "<" with the callback data "notifications_{page - 1}" (if the current page is not 0).
    - A button labeled "Delete" with the callback data "notification_delete_{curent_uuid}".
    - A button labeled ">" with the callback data "notifications_{page + 1}".
    The buttons are arranged in a specific layout using the InlineKeyboardBuilder.
    Returns the constructed InlineKeyboardMarkup.
    """
    markup = InlineKeyboardBuilder()
    if page > 0:
        markup.button(text="<", callback_data=f"notifications_{page - 1}")
    markup.button(text="Delete", callback_data=f"notification_delete_{curent_uuid}")
    markup.button(text=">", callback_data=f"notifications_{page + 1}")
    markup.button(text="Go to menu", callback_data="go_menu")
    markup.adjust(3, 1, 1)
    if page == 0:
        markup.adjust(2, 1, 1)
    return markup.as_markup()

def cancel_form():
    """
    Returns an InlineKeyboardMarkup with a single button labeled "Cancel" with the callback data "cancel_form".
    """
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Cancel", callback_data="cancel_form")]])


def protocols():
    """
    Returns an InlineKeyboardMarkup with buttons for each protocol.
    """
    # Create protocol selection buttons
    markup = InlineKeyboardBuilder()
    for protocol in ProtocolIDs:
        markup.button(text=protocol.name, callback_data=f"protocol_{protocol.value}")
    markup.button(text="Cancel", callback_data="cancel_form")
    return markup.as_markup()
