""" Base class for collectors. """
from abc import ABC, abstractmethod


class Collector(ABC):
    """
    Base class for collectors.

    :method: `collect_data` -> Collects data from the specified storage.
    """

    @abstractmethod
    def collect_data(self, *args, **kwargs):
        """fn docstring"""
        pass
