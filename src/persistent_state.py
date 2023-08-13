import pickle
import subprocess
import sys

import pandas
import requests
import streamlit

import src.classes
import src.constants
import src.db


LATEST_BLOCK_FILENAME = "persistent-state-keeper.txt"
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
            return src.classes.State()
    else:
        print(f"Failed to download file. Status code: {response.status_code}")
        return src.classes.State()


def get_persistent_filename(block_number):
    return f"persistent-state-{block_number}.pckl"


def load_persistent_state():
    latest_block = int(open(LATEST_BLOCK_FILENAME, "r").read())
    file = open(get_persistent_filename(latest_block), "rb")
    state = pickle.load(file)
    file.close()
    if "latest_block" not in streamlit.session_state:
        streamlit.session_state["latest_block"] = latest_block
        print("Updated latest block from persistent state to", latest_block)
    if "state" not in streamlit.session_state:
        streamlit.session_state["state"] = state
        print("Updated state from persistent state")


def check_gsutil_exists():
    try:
        subprocess.check_output(["gsutil", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def upload_state_as_pickle(state):
    with open(PERSISTENT_STATE_FILENAME, "wb") as out_file:
        pickle.dump(state, out_file)
    if upload_file_to_bucket(PERSISTENT_STATE_FILENAME):
        msg = "Successfully uploaded state to GCP"
    else:
        msg = "Failed uploading state to GCP"

    print(msg, flush=True)


def upload_file_to_bucket(filename):
    bucket_name = "derisk-persistent-state"
    command = ["gsutil", "-m", "cp", "-c"]
    command.extend([filename, f"gs://{bucket_name}/{filename}"])
    try:
        subprocess.check_call(command)
        return True
    except subprocess.SubprocessError as error:
        print(error)
        return False


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

    if check_gsutil_exists():
        print("gsutil found")
    else:
        print("did not find gsutil, aborting")
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

    state = src.classes.State()
    for _, event in zklend_events.iterrows():
        state.process_event(event=event)

    state.update_block_number(persistent_block_number)

    with open(PERSISTENT_STATE_FILENAME, "wb") as out_file:
        pickle.dump(state, out_file)

    print("Created new persistent_state with latest block", persistent_block_number)

    if upload_file_to_bucket(PERSISTENT_STATE_FILENAME):
        print("Uploaded new state to GCP")
    else:
        print("Failed uploading new state to GCP")


if __name__ == "__main__":
    main()
