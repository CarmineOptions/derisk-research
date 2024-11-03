""" This module contains the data collectors for the liquidable debt data handler. """
from typing import Iterable

import dask.dataframe as dd
from data_handler.handlers.liquidable_debt.bases import Collector
from data_handler.handlers.liquidable_debt.exceptions import ProtocolExistenceError
from data_handler.handlers.liquidable_debt.managers import LocalStorageManager


class GoogleCloudDataCollector(Collector):
    """class docstring"""
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
        Collects data from Google Cloud Storage bucket and saves it to local storage.
        :param protocol_name: The protocol to collect data from.
        :param available_protocols: The available protocols to collect data from.
        :param bucket_name: The bucket name to collect data from. (Google Cloud Storage Bucket Name)
        :param path: The path where the data will be saved to (Local Storage Path).
        :param url: The connection URL to collect data from (Google Cloud Storage Bucket url).
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
        Downloads parquet file to local storage from Google Cloud Storage
        :param protocol_name: Protocol name
        :param bucket_name: Google Cloud Storage bucket name
        :param path: Local storage path to download file
        :return: None
        """

        data = dd.read_parquet(url.format(bucket_name=bucket_name, protocol_name=protocol_name))
        dd.to_parquet(df=data, path=path.format(protocol_name=protocol_name))

    @classmethod
    def _remove_file(cls, file_path: str) -> None:
        """
        Removes file from local storage
        :param file_path: Local storage path to remove
        :return: None
        """
        cls.LS_MANAGER.delete_file(file_path)

    @classmethod
    def _check_protocol_existence(
        cls, protocol_name: str, available_protocols: Iterable[str]
    ) -> None:
        """
        Checks if protocol exists
        :param protocol_name: Protocol name
        :param available_protocols: Available protocols
        :return: None
        """
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
        """
        Checks if the protocol name is in available protocols list
        :param protocol_name: Protocol name
        :param available_protocols: Available protocols
        :return: True if protocol exists else False
        """
        return protocol_name in available_protocols


class DBDataCollector(Collector):
    """class docstring"""
    # TODO write logic when it will be needed
    def collect_data(self):
        pass
