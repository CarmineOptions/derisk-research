import os
import shutil
from typing import Iterable


class LocalStorageManager:
    """
    A manager that stores liquidable debts in local storage.

    :method: `update_dir` -> Updates the local storage directory.
                            Deletes the local storage directory if it already exists.
    """
    @classmethod
    def update_dir(cls, protocol_name: str) -> str:
        if file_path := f"{protocol_name}_data" in os.listdir("liquidable_debt/loans/"):
            cls._delete_file(f"liquidable_debt/loans/{file_path}")

        os.mkdir(f"liquidable_debt/loans/{protocol_name}_data/")

        return file_path

    @staticmethod
    def _delete_file(file_path: str) -> None:
        """
        Deletes parquet file from local storage including the directory it's stored in.
        :param file_path: str
        :return: None
        """
        shutil.rmtree(file_path)
