"""
Defines the base class for data collectors.
"""

from abc import ABC, abstractmethod


class Collector(ABC):
    """
    Abstract base class for data collectors.
    """

    @abstractmethod
    def collect_data(self, *args, **kwargs):
        """Abstract method to collect data from a specified storage."""
        pass
