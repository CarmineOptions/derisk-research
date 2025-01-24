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
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")

        self.conn = None
        self.cur = None
        self.connect_to_db()

    def connect_to_db(self):
        """
        Make connection to the PostgreSQL DB and set the connection and cursor.

        Returns:
            None
        """
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port
                   
                )
                self.cur = self.conn.cursor()
            except psycopg2.DatabaseError as e:
                logging.error(e)
                raise e
            finally:
                logging.info('Connection opened successfully.')

    def get_user_debt(self, protocol_id: str, wallet_id: str) -> float | None:
        """
        Fetches user debt for a given protocol and wallet.

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
        Fetches user collateral for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID
            wallet_id (str): User wallet ID.

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
        Fetches user loan state for a given protocol and wallet.

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
        Closes the database connection if open.
        """
        if self.conn:
            self.cur.close()
            self.conn.close()
            logging.info("PostgreSQL connection closed.")

