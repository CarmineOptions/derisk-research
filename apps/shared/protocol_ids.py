from enum import Enum


class ProtocolIDs(Enum):
    """
    This class contains the protocol IDs that are used in the system.
    """

    HASHSTACK = "Hashstack"
    NOSTRA_ALPHA = "Nostra_alpha"
    NOSTRA_MAINNET = "Nostra_mainnet"
    ZKLEND = "zkLend"
    VESU = "Vesu"

    # @classmethod
    # def choices(cls) -> list[str]:
    #     """
    #     This method returns the values of the enum.
    #     :return: list of values
    #     """
    #     return [choice.value for choice in cls]
