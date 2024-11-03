""" This module contains the manager for liquidable debts. """
import os
import shutil


class LocalStorageManager:
    """
    A manager that stores liquidable debts in local storage.

    :method: `update_dir` -> Updates the local storage directory.
                            Deletes the local storage directory if it already exists.
    """

    @classmethod
    def update_dir(cls, protocol_name: str) -> str:
        """
        Updates the local storage directory.
        :param protocol_name: The protocol name.
        :return: The updated local storage directory path.
        """
        current_directory = os.getcwd()
        if "loans" not in os.listdir(current_directory):
            os.mkdir("loans")

            return f"{current_directory}/loans"

        dirs = os.listdir(current_directory + "/loans")
        for file_path in dirs:
            if file_path in os.listdir("loans"):
                cls._delete_file(f"loans/{file_path}")

        os.mkdir(f"loans/{protocol_name}_data/")

        return f"loans/{protocol_name}_data/"

    @staticmethod
    def _delete_file(file_path: str) -> None:
        """
        Deletes parquet file from local storage including the directory it's stored in.
        :param file_path: str
        :return: None
        """
        shutil.rmtree(file_path)
