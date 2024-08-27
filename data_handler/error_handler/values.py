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


class ProtocolIDs(Enum):
    """
    Enum class for protocol identifiers.

    :cvar NOSTRA_ALPHA: The Nostra Alpha protocol identifier.
    :cvar NOSTRA_MAINNET: The Nostra Mainnet protocol identifier.
    :cvar ZKLEND: The zkLend protocol identifier.
    """

    NOSTRA_ALPHA: str = "Nostra_alpha"
    NOSTRA_MAINNET: str = "Nostra_mainnet"
    ZKLEND: str = "zkLend"
