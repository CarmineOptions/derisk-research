from error_handler.values import MessageTemplates


class TokenSettingsNotFound(Exception):
    """
    Exception class raised when the token settings are not found.
    """

    def __init__(self, address: str, protocol: str):
        self.address = address
        self.protocol = protocol

    def __str__(self):
        return MessageTemplates.NEW_TOKEN_MESSAGE.format(
            address=self.address, protocol_name=self.protocol
        )
