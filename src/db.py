import os

import psycopg2

import src.constants


PG_CONNECTION_STRING = os.environ.get("PG_CONNECTION_STRING")

if PG_CONNECTION_STRING is None:
    print("No PG connection string, aborting", flush=True)
    exit(1)


def establish_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(PG_CONNECTION_STRING)


def run_query(query, conn: psycopg2.extensions.connection):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def format_starkscan_event(event):
    # event structure: https://starkscan.readme.io/reference/event-object
    return {
        "block_hash": event[0],
        "block_number": event[1],
        "transaction_has": event[2],
        "event_index": event[3],
        "from_address": event[4],
        "keys": event[5],
        "data": event[6],
        "timestamp": event[7],
        "key_name": event[8],
    }


def get_events(protocol: src.constants.Protocol, conn: psycopg2.extensions.connection):
    return list(
        map(
            format_starkscan_event,
            run_query(
                f"""
        SELECT
            block_hash, block_number, transaction_hash, event_index, from_address, keys, data, timestamp, key_name
        FROM
            {src.constants.Table.EVENTS.value}
        WHERE
            from_address='{protocol.value}';
        """,
                conn,
            ),
        )
    )


def get_events_by_key_name(
    protocol: src.constants.Protocol, key_name: str, conn: psycopg2.extensions.connection
):
    return list(
        map(
            format_starkscan_event,
            run_query(
                f"""
        SELECT
            block_hash, block_number, transaction_hash, event_index, from_address, keys, data, timestamp, key_name
        FROM
            {src.constants.Table.EVENTS.value}
        WHERE
            from_address='{protocol.value}' and key_name='{key_name}';
        """,
                conn,
            ),
        )
    )
