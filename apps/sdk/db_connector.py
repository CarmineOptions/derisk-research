import psycopg2
from dotenv import load_dotenv
import os
import logging

load_dotenv()

class DBConnector:
    """
    DBConnector manages PostgreSQL database connection and operations.

    Methods:
        get_user_debt(protocol_id: str, wallet_id: str) -> float | None: Fetches user debt.
        get_user_collateral(protocol_id: str, wallet_id: str) -> float | None: Fetches user collateral.
        get_loan_state(protocol_id: str, wallet_id: str) -> str | None: Fetches loan state.
        close_connection() -> None: Closes the database connection.
    """

    def __init__(self):
        """
        Initializes DBConnector by connecting to the PostgreSQL database.
        """
        self.conn, self.cur = self.connect_to_db()

    def connect_to_db(self):
        """
        make  connection to the PostgreSQL DB and returns the connection and cursor.

        Returns:
            tuple: (conn, cur) where conn is  connection object and cur is  cursor object.
        """
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        try:
            conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            cur = conn.cursor()
            logging.info("Connected to PostgreSQL successfully.")
            return conn, cur
        except (Exception, psycopg2.Error) as error:
            logging.info(f"Error while connecting to PostgreSQL: {error}")
            raise

    def get_user_debt(self, protocol_id: str, wallet_id: str) -> float | None:
        """
        fetches  user debt for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            float | None: User debt if found, otherwise None.
        """
        try:
            sql = """
                SELECT debt 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            return result[0] if result else None
        except (Exception, psycopg2.Error) as error:
            logging.info(f"Error while fetching user debt: {error}")
            raise

    def get_user_collateral(self, protocol_id: str, wallet_id: str) -> float | None:
        """
        fetches user collateral for a given protocol and wallet.

        Args:
            protocol_id (str): protocol ID
            wallet_id (str): user wallet ID.

        Returns:
            float | None: User collateral if found, otherwise None.
        """
        try:
            sql = """
                SELECT collateral 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            return result[0] if result else None
        except (Exception, psycopg2.Error) as error:
            logging.info(f"Error while fetching user collateral: {error}")
            raise

    def get_loan_state(self, protocol_id: str, wallet_id: str) -> str | None:
        """
        fetches  user loan state for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            str | None: User's loan state if found, otherwise None.
        """
        try:
            sql = """
                SELECT loan_state 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            return result[0] if result else None
        except (Exception, psycopg2.Error) as error:
            logging.info(f"Error while fetching user loan state: {error}")
            raise

    def close_connection(self) -> None:
        """
        closes the database connection if open.
        """
        if self.conn:
            self.cur.close()
            self.conn.close()
            logging.info("PostgreSQL connection closed.")
