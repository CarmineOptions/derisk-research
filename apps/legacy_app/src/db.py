import logging
import os

import psycopg2


# PG_CONNECTION_STRING can be or some <value> or "" but not `None`
PG_CONNECTION_STRING = os.environ.get("PG_CONNECTION_STRING", "")

def establish_connection() -> psycopg2.extensions.connection:
    """
    Establishes a connection to the PostgreSQL database.
    :return: psycopg2 connection object
    """
    try:
        return psycopg2.connect(PG_CONNECTION_STRING)
    except psycopg2.OperationalError:
        logging.info(f"Failed to establish connection to PostgreSQL with PG_CONNECTION_STRING: {PG_CONNECTION_STRING}")
        exit(1)
