"""
This is module connects to a PostgreSQL database and fetches data.
"""

import logging
import os
from typing import Optional

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from shared.exceptions.db import DatabaseConnectionError

load_dotenv()

logger = logging.getLogger(__name__)


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

    VESU_POSITIONS_SQL_QUERY = """
        SELECT
            vp.user,
            vp.pool_id,
            vp.collateral_asset,
            vp.debt_asset,
            vp.block_number
        FROM
            vesu_positions AS vp
        WHERE
            vp.block_number = (
                SELECT MAX(block_number)
                FROM vesu_positions
                WHERE user = vp.user
                AND pool_id = vp.pool_id
            );
    """

    VESU_HEALTH_FACTORS_SQL_QUERY = """
        SELECT
            hrl.user_id as user,
            hrl.protocol_id as pool_id,
            hrl.value as health_factor,
            hrl.timestamp
        FROM
            health_ratio_level AS hrl
        WHERE
            hrl.timestamp = (
                SELECT MAX(timestamp)
                FROM health_ratio_level
                WHERE user_id = hrl.user_id
                AND protocol_id = hrl.protocol_id
            );
    """

    def __init__(self):
        """
        Initialize the DataConnector with database connection details.
        """
        self._check_env_variables()
        self.db_url = (
            f"postgresql://"
            f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.engine = sqlalchemy.create_engine(self.db_url)

    def fetch_data(
        self,
        query: str,
        protocol: Optional[str] = None,
        batch_size: int = 1000,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch data from the database using a SQL query with block-based pagination.

        :param query: SQL query to execute.
        :param batch_size: Number of blocks to process in each batch
        :param start_block: Starting block number for filtering (optional)
        :param end_block: Ending block number for filtering (optional)
        :param protocol: Protocol identifier for determining block range (optional)
        :return: DataFrame containing the query results
        """
        # If protocol is provided and block range is not, determine block range automatically
        if protocol:
            if start_block is None:
                start_block = self.fetch_protocol_first_block_number(protocol)
            if end_block is None:
                end_block = self.fetch_protocol_last_block_number(protocol)

        # Ensure we have valid block range
        if start_block is None or end_block is None:
            logger.warning(
                "No block range provided and no protocol specified to determine range"
            )
            # Execute the query without any block-based pagination
            try:
                with self.engine.connect() as connection:
                    return pd.read_sql(query, connection)
            except sqlalchemy.exc.SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseConnectionError(f"Failed to execute query: {str(e)}")

        all_data = []
        clean_query = query.strip()
        if clean_query.endswith(";"):
            clean_query = clean_query[:-1]

        # Check if query already contains block filters
        if "block >= " in clean_query or "block <= " in clean_query:
            logger.warning("Query already contains block filters, using as-is")
            with self.engine.connect() as connection:
                return pd.read_sql(query, connection)

        for current_start in range(start_block, end_block + 1, batch_size):
            current_end = min(current_start + batch_size - 1, end_block)

            # Check if query contains WHERE clause to determine how to add block filtering
            if "WHERE" in clean_query.upper():
                block_query = f"{clean_query} AND block >= {current_start} AND block <= {current_end};"
            else:
                block_query = sqlalchemy.text(
                    f"{clean_query} WHERE block >= :start_block AND block <= :end_block"
                )

            try:
                with self.engine.connect() as connection:
                    batch = pd.read_sql(
                        block_query,
                        connection,
                        params={"start_block": current_start, "end_block": current_end},
                    )

                if not batch.empty:
                    all_data.append(batch)
                else:
                    logger.info(
                        f"No records found in block range {current_start}-{current_end}"
                    )

            except sqlalchemy.exc.SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseConnectionError(f"Failed to execute query: {str(e)}")

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    def fetch_protocol_first_block_number(self, protocol: str) -> int:
        """
        Fetch the first block number for a specific protocol.

        :param protocol: Protocol identifier (e.g., 'zkLend').
        :return: First block number
        """
        query = """
            SELECT MIN(block) as first_block
            FROM loan_state 
            WHERE protocol_id = :protocol;
        """
        with self.engine.connect() as connection:
            result = pd.read_sql(
                sqlalchemy.text(query), connection, params={"protocol": protocol}
            )
            if not result.empty and not pd.isna(result["first_block"].iloc[0]):
                return int(result["first_block"].iloc[0])
            return 0

    def fetch_protocol_last_block_number(self, protocol: str) -> int:
        """
        Fetch the last block number for a specific protocol.

        :param protocol: Protocol identifier (e.g., 'zkLend').
        :return: Last block number as an integer.
        """
        query = """
            SELECT MAX(block) as last_block
            FROM loan_state 
            WHERE protocol_id = :protocol;
        """
        with self.engine.connect() as connection:
            result = pd.read_sql(
                sqlalchemy.text(query), connection, params={"protocol": protocol}
            )
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
            logger.error(f"Error reading CSV file: {e}")
            return None

    def fetch_vesu_positions(self) -> pd.DataFrame:
        """
        Fetch Vesu positions data using the predefined query.

        :return: DataFrame containing Vesu positions data
        """
        try:
            with self.engine.connect() as connection:
                return pd.read_sql(self.VESU_POSITIONS_SQL_QUERY, connection)
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to fetch Vesu positions: {str(e)}")

    def fetch_vesu_health_factors(self) -> pd.DataFrame:
        """
        Fetch Vesu health factors data using the predefined query.

        :return: DataFrame containing Vesu health factors data
        """
        try:
            with self.engine.connect() as connection:
                return pd.read_sql(self.VESU_HEALTH_FACTORS_SQL_QUERY, connection)
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(
                f"Failed to fetch Vesu health factors: {str(e)}"
            )


class DataConnectorAsync(DataConnector):
    """
    Handles database connection and fetches data asynchronously.
    """

    async def fetch_data(
        self,
        query: str,
        protocol: Optional[str] = None,
        batch_size: int = 1000,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Asynchronously fetch data from the database using a SQL query with block-based pagination.

        :param query: SQL query to execute.
        :param batch_size: Number of blocks to process in each batch
        :param start_block: Starting block number for filtering (optional)
        :param end_block: Ending block number for filtering (optional)
        :param protocol: Protocol identifier for determining block range (optional)
        :return: DataFrame containing the query results
        """
        # If protocol is provided and block range is not, determine block range automatically
        if protocol:
            if start_block is None:
                start_block = await self.fetch_protocol_first_block_number(protocol)
            if end_block is None:
                end_block = await self.fetch_protocol_last_block_number(protocol)

        # Ensure we have valid block range
        if start_block is None or end_block is None:
            logger.warning(
                "No block range provided and no protocol specified to determine range"
            )
            # Execute the query without any block-based pagination
            try:
                with self.engine.connect() as connection:
                    return pd.read_sql(query, connection)
            except sqlalchemy.exc.SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseConnectionError(f"Failed to execute query: {str(e)}")

        all_data = []
        clean_query = query.strip()
        if clean_query.endswith(";"):
            clean_query = clean_query[:-1]

        # Check if query already contains block filters
        if "block >= " in clean_query or "block <= " in clean_query:
            logger.warning("Query already contains block filters, using as-is")
            with self.engine.connect() as connection:
                return pd.read_sql(query, connection)

        for current_start in range(start_block, end_block + 1, batch_size):
            current_end = min(current_start + batch_size - 1, end_block)

            # Check if query contains WHERE clause to determine how to add block filtering
            if "WHERE" in clean_query.upper():
                block_query = f"{clean_query} AND block >= {current_start} AND block <= {current_end};"
            else:
                block_query = sqlalchemy.text(
                    f"{clean_query} WHERE block >= :start_block AND block <= :end_block"
                )

            try:
                with self.engine.connect() as connection:
                    batch = pd.read_sql(
                        block_query,
                        connection,
                        params={"start_block": current_start, "end_block": current_end},
                    )

                if not batch.empty:
                    all_data.append(batch)
                else:
                    logger.info(
                        f"No records found in block range {current_start}-{current_end}"
                    )

            except sqlalchemy.exc.SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseConnectionError(f"Failed to execute query: {str(e)}")

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    async def fetch_protocol_first_block_number(self, protocol: str) -> int:
        """
        Asynchronously fetch the first block number for a specific protocol.

        :param protocol: Protocol identifier (e.g., 'zkLend').
        :return: First block number
        """
        query = """
            SELECT MIN(block) as first_block
            FROM loan_state 
            WHERE protocol_id = :protocol;
        """
        with self.engine.connect() as connection:
            result = pd.read_sql(
                sqlalchemy.text(query), connection, params={"protocol": protocol}
            )
            if not result.empty and not pd.isna(result["first_block"].iloc[0]):
                return int(result["first_block"].iloc[0])
            return 0

    async def fetch_protocol_last_block_number(self, protocol: str) -> int:
        """
        Asynchronously fetch last block number for a specific protocol.

        :param protocol: Protocol identifier (e.g., 'zkLend').
        :return: Last block number as an integer.
        """
        query = """
            SELECT MAX(block) as last_block
            FROM loan_state 
            WHERE protocol_id = :protocol;
        """
        with self.engine.connect() as connection:
            result = pd.read_sql(
                sqlalchemy.text(query), connection, params={"protocol": protocol}
            )
            if not result.empty and not pd.isna(result["last_block"].iloc[0]):
                return int(result["last_block"].iloc[0])
            return 0


if __name__ == "__main__":
    connector = DataConnector()
    df = connector.fetch_data(DataConnector.ZKLEND_SQL_QUERY, "zkLend")
    print(df)
