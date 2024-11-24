import os

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()


class DataConnector:
    REQUIRED_VARS = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    ZKLEND_SQL_QUERY = """
        SELECT
            ls.block,
            ls.user,
            ls.collateral,
            ls.debt,
            zcd.collateral_enabled
        FROM
            loan_state AS ls
        JOIN
            zklend_collateral_debt AS zcd
        ON
            ls.user = zcd.user_id
        WHERE
            ls.protocol_id = 'zkLend';
    """
    ZKLEND_INTEREST_RATE_SQL_QUERY = """
        WITH max_block AS (
            SELECT MAX(block) AS max_block
            FROM interest_rate
            WHERE protocol_id = 'zkLend'
        )
        SELECT collateral, debt, block 
        FROM interest_rate
        WHERE protocol_id = 'zkLend' AND block = (SELECT max_block FROM max_block);
    """

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

    def fetch_data(self, query: str) -> pd.DataFrame:
        """
        Fetch data from the database using a SQL query.

        :param query: SQL query to execute.
        :return: DataFrame containing the query results
        """
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
