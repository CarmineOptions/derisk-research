import pickle
import sys
from google.cloud import storage
import pandas
import requests

import src.constants
import src.db
import src.zklend


PERSISTENT_STATE_FILENAME = "persistent-state.pckl"


def download_and_load_state_from_pickle():
    response = requests.get(
        "https://storage.googleapis.com/derisk-persistent-state/persistent-state.pckl"
    )
    if response.status_code == 200:
        try:
            state = pickle.loads(response.content)
            return state
        except pickle.UnpicklingError as e:
            print("Failed to unpickle the data:", e)
            return src.zklend.State()
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
        return src.zklend.State()


def upload_state_as_pickle(state):
    with open(PERSISTENT_STATE_FILENAME, "wb") as out_file:
        pickle.dump(state, out_file)
    upload_file_to_bucket(PERSISTENT_STATE_FILENAME, PERSISTENT_STATE_FILENAME)


def upload_file_to_bucket(source, target):
    bucket_name = "derisk-persistent-state"

    # Initialize the Google Cloud Storage client with the credentials
    storage_client = storage.Client.from_service_account_json(
        "storage_credentials.json")

    # Get the target bucket
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket
    blob = bucket.blob(target)
    blob.upload_from_filename(source)

    print(
        f"File {source} uploaded to gs://{bucket_name}/{target}")


def main():
    # Check if the number argument is provided
    if len(sys.argv) < 2:
        print("Specify persistent block number")
        sys.exit(1)

    # Get the number argument from the command-line
    number_str = sys.argv[1]

    try:
        # Try to convert the number argument to an integer
        persistent_block_number = int(sys.argv[1])
    except ValueError:
        print("Invalid persistent block number:", number_str)
        sys.exit(1)

    connection = src.db.establish_connection()

    # Load all Zklend events.
    zklend_events = pandas.read_sql(
        sql=f"""
    SELECT
        *
    FROM
        starkscan_events
    WHERE
        from_address='{src.constants.Protocol.ZKLEND.value}'
    AND
        key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
    AND
        block_number<{persistent_block_number}
    ORDER BY
        block_number, id ASC;
    """,
        con=connection,
    )

    # Close the connection.
    connection.close()

    zklend_events.set_index("id", inplace=True)

    state = src.zklend.State()
    for _, event in zklend_events.iterrows():
        state.process_event(event=event)

    state.update_block_number(persistent_block_number)

    with open(PERSISTENT_STATE_FILENAME, "wb") as out_file:
        pickle.dump(state, out_file)

    print("Created new persistent_state with latest block", persistent_block_number)

    upload_file_to_bucket(PERSISTENT_STATE_FILENAME, PERSISTENT_STATE_FILENAME)


if __name__ == "__main__":
    main()
