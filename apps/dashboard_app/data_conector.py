"""
This is module connects to a PostgreSQL database and fetches data. 
"""

import os

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()


class DataConnector:
    """
    Handles database connection and fetches data.
    """

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

    def fetch_data(self, query: str, batch_size: int = 1000) -> pd.DataFrame:
        """
        Fetch data from the database using a SQL query.

        :param query: SQL query to execute.
        :param batch_size: Number of records to fetch per batch. If None, fetches all data at once.
        :return: DataFrame containing the query results
        """
        all_data = []
        offset = 0

        while True:
            # Use the original query if it already contains LIMIT and OFFSET
            if "LIMIT" not in query.upper() and "OFFSET" not in query.upper():
                clean_query = query.strip()
                if clean_query.endswith(";"):
                    clean_query = clean_query[:-1]
                paginated_query = f"{clean_query} LIMIT {batch_size} OFFSET {offset}"
            else:
                paginated_query = query

            try:
                with self.engine.connect() as connection:
                    batch = pd.read_sql(paginated_query, connection)

                if batch.empty:
                    break

                all_data.append(batch)
                offset += batch_size

                if len(batch) < batch_size:
                    break

            except Exception as e:
                print(f"Error executing batch query: {e}")
                break

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    def fetch_protocol_last_block_number(self, protocol: str) -> int:
        """
        Fetch the last block number for a specific protocol.

        :param protocol: Protocol identifier (e.g., 'zkLend').
        :return: Last block number as an integer.
        """
        query = f"""
            SELECT MAX(block) as last_block
            FROM loan_state 
            WHERE protocol_id = '{protocol}';
        """

        with self.engine.connect() as connection:
            result = pd.read_sql(query, connection)
            if not result.empty and not pd.isna(result["last_block"].iloc[0]):
                return int(result["last_block"].iloc[0])
            return 0

    def _check_env_variables(self) -> None:
        """
        Check if all required environment variables are set.

        :raises EnvironmentError: If any required environment variable is missing.
        """
        for var in self.REQUIRED_VARS:
            if os.getenv(var) is None:
                raise EnvironmentError(f"Environment variable {var} is not set.")

    def fetch_data_from_csv(self, file_path: str) -> pd.DataFrame:
        """
        Fetch data from a CSV file.

        :param file_path: Path to the CSV file.
        :return: DataFrame containing the data from the CSV file.
        """
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None


if __name__ == "__main__":
    connector = DataConnector()
    df = connector.fetch_data("loan_state", "zkLend")
    print(df)
