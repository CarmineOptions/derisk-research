"""
Data collectors for retrieving and managing protocol 
data from Google Cloud Storage and databases.
"""

from typing import Iterable
import dask.dataframe as dd
from data_handler.handlers.liquidable_debt.bases import Collector
from data_handler.handlers.liquidable_debt.exceptions import ProtocolExistenceError
from data_handler.handlers.liquidable_debt.managers import LocalStorageManager


class GoogleCloudDataCollector(Collector):
    """
    Collector for retrieving protocol data 
    from Google Cloud Storage and saving it locally.
    """

    LS_MANAGER = LocalStorageManager

    @classmethod
    def collect_data(
        cls,
        protocol_name: str,
        available_protocols: Iterable[str],
        bucket_name: str,
        path: str,
        url: str,
    ) -> str:
        """
        Collects data from Google Cloud Storage 
        bucket and saves it to local storage.
        """
        cls._check_protocol_existence(protocol_name, available_protocols)

        file_name = cls.LS_MANAGER.update_dir(protocol_name)

        cls._download_file(
            protocol_name=protocol_name,
            bucket_name=bucket_name,
            path=path,
            url=url,
        )

        return file_name

    @staticmethod
    def _download_file(
        protocol_name: str,
        bucket_name: str,
        url: str,
        path: str,
    ) -> None:
        """
        Downloads parquet file to local 
        storage from Google Cloud Storage.
        """
        data = dd.read_parquet(
            url.format(bucket_name=bucket_name, protocol_name=protocol_name)
        )
        dd.to_parquet(df=data, path=path.format(protocol_name=protocol_name))

    @classmethod
    def _remove_file(cls, file_path: str) -> None:
        """Removes file from local storage."""
        cls.LS_MANAGER.delete_file(file_path)

    @classmethod
    def _check_protocol_existence(
        cls, protocol_name: str, available_protocols: Iterable[str]
    ) -> None:
        """Checks if the specified protocol exists 
        in the list of available protocols."""
        if not cls._protocol_exists(
            protocol_name=protocol_name,
            available_protocols=available_protocols,
        ):
            raise ProtocolExistenceError(protocol=protocol_name)

    @staticmethod
    def _protocol_exists(
        protocol_name: str,
        available_protocols: Iterable[str],
    ) -> bool:
        """Checks if the protocol name is in the list of available protocols."""
        return protocol_name in available_protocols


class DBDataCollector(Collector):
    """Placeholder collector for retrieving data from the database."""
    
    def collect_data(self):
        pass
