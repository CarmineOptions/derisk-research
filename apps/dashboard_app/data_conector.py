import os

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

from shared.constants import ZKLEND

load_dotenv()


class DataConnector:
    REQUIRED_VARS = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    SQL_QUERY = f"SELECT * FROM %s WHERE protocol_id = '{ZKLEND}'"

    def __init__(self):
        """
        Initialize the DataHandler with database connection details.
        """
        self._check_env_variables()
        self.db_url = (
            f"postgresql://"
            f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.engine = sqlalchemy.create_engine(self.db_url)

    def fetch_data(self, table_name: str, protocol_id: str) -> pd.DataFrame:
        """
        Fetch data from the database using a SQL query.

        :param table_name: Name of the table to fetch data from.
        :param protocol_id: ID of the protocol to fetch data for.
        :return: DataFrame containing the query results
        """
        query = self.SQL_QUERY % (table_name,)
        with self.engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df

    def _check_env_variables(self) -> None:
        """
        Check if all required environment variables are set.

        :raises EnvironmentError: If any required environment variable is missing.
        """
        for var in self.REQUIRED_VARS:
            if os.getenv(var) is None:
                raise EnvironmentError(f"Environment variable {var} is not set.")


if __name__ == "__main__":
    connector = DataConnector()
    df = connector.fetch_data("loan_state", "zkLend")
    print(df)
