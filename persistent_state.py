import pickle
import subprocess
import sys
import pandas

import constants
import db
import classes
import streamlit as st


LATEST_BLOCK_FILENAME = "persistent-state-keeper.txt"


def get_persistent_filename(block_number):
    return f"persistent-state-{block_number}.pckl"


def load_persistent_state():
    latest_block = int(open(LATEST_BLOCK_FILENAME, "r").read())
    file = open(get_persistent_filename(latest_block), "rb")
    state = pickle.load(file)
    file.close()
    if "latest_block" not in st.session_state:
        st.session_state["latest_block"] = latest_block
        print("Updated latest block from persistent state to", latest_block)
    if "state" not in st.session_state:
        st.session_state["state"] = state
        print("Updated state from persistent state")


def check_gsutil_exists():
    try:
        subprocess.check_output(["gsutil", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


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

    connection = db.establish_connection()

    # Load all Zklend events.
    zklend_events = pandas.read_sql(
        sql=f"""
    SELECT
        *
    FROM
        starkscan_events
    WHERE
        from_address='{constants.Protocol.ZKLEND.value}'
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

    state = classes.State()
    for _, event in zklend_events.iterrows():
        state.process_event(event=event)

    persistent_state_filename = get_persistent_filename(persistent_block_number)
    with open(persistent_state_filename, "wb") as out_file:
        pickle.dump(state, out_file)

    with open(LATEST_BLOCK_FILENAME, "w") as f:
        f.write(str(persistent_block_number))

    print("Created new persistent_state with latest block", persistent_block_number)

    if upload_file_to_bucket(persistent_state_filename):
        print("Uploaded new state to GCP")
    else:
        print("Failed uploading new state to GCP")


if __name__ == "__main__":
    main()
