class ProtocolExistenceError(Exception):
    def __init__(self, protocol: str = None, *args):
        super().__init__(args)
        self.protocol = protocol

    def __str__(self):
        return f"\"{self.protocol}\" is not in a valid protocol!"


class TokenValidationError(Exception):
    pass
