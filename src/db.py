import os

import psycopg2



PG_CONNECTION_STRING = os.environ.get("PG_CONNECTION_STRING")
if PG_CONNECTION_STRING is None:
    print("No PG connection string, aborting.", flush=True)
    exit(1)



def establish_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(PG_CONNECTION_STRING)