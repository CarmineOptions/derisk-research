""" This module contains the exceptions that can be raised by the liquidable_debt handler."""

class ProtocolExistenceError(Exception):
    """
    An exception that should be raised when a given protocol doesn't exist.

    :arg protocol: The protocol name that doesn't exist.
    """

    def __init__(self, protocol: str):
        self.protocol = protocol

    def __str__(self):
        return f"Protocol {self.protocol} doesn't exist. Please provide a valid protocol name."
