from dataclasses import dataclass
from enum import Enum


@dataclass
class Message:
    text: str
    is_sent: bool


@dataclass
class MessageTemplates:
    """
    Dataclass for messages.

    :cvar ENTRY_MESSAGE: The entry message.
    :cvar NEW_TOKEN_MESSAGE: The message indicating that a new token has been added
    """

    ENTRY_MESSAGE: str = "Now you will recieve notifications if any error occurs."
    RETRY_ENTRY_MESSAGE: str = "You have already registered for error notifications."
    NEW_TOKEN_MESSAGE: str = "{protocol_name} has a new token with address {address}."
