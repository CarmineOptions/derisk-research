from enum import Enum

class ProtocolIDs(Enum):
    HASHSTACK: str = "Hashstack"
    NOSTRA_ALPHA: str = "Nostra_alpha"
    NOSTRA_MAINNET: str = "Nostra_mainnet"
    ZKLEND: str = "zkLend"
    VESU:str = "Vesu"

    @classmethod
    def choices(cls) -> list[str]:
        """
        This method returns the values of the enum.
        :return: list of values
        """
        return [choice.value for choice in cls]