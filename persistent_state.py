import os
import pickle
import subprocess
import sys
import pandas

import constants
import db
import classes
import glob
import streamlit as st


def load_persistent_state():
    if "initial_state" not in st.session_state:
        st.session_state["initial_state"] = True
        matching_files = glob.glob("persistent-state-*.pckl")
        if matching_files:
            file_name = matching_files[0]
            latest_block = int(file_name[len("persistent-state-") : -len(".pckl")])
            file = open(file_name, "rb")
            state = pickle.load(file)
            file.close()
            if "latest_block" not in st.session_state:
                st.session_state["latest_block"] = latest_block
                print("Updated latest block from persistent state to", latest_block)
            if "state" not in st.session_state:
                st.session_state["state"] = state
                print("Updated state from persistent state")
        else:
            print("No matching file found.")


def check_gsutil_exists():
    try:
        subprocess.check_output(["gsutil", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False


def upload_file_to_bucket():
    file_path = "persistent-state.pckl"
    bucket_name = "derisk-persistent-state"
    destination_path = "persistent-state.pckl"
    command = ["gsutil", "-m", "cp", "-c"]
    command.extend([file_path, f"gs://{bucket_name}/{destination_path}"])
    subprocess.call(command)


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

    file_name = "persistent-state.pckl"

    state = classes.State()
    for _, event in zklend_events.iterrows():
        state.process_event(event=event)

    if os.path.isfile(file_name):
        os.remove(file_name)

    print("Deleted old persistent state")

    with open(file_name, "wb") as out_file:
        pickle.dump(state, out_file)

    print("Created new persistent_state with latest block", persistent_block_number)

    upload_file_to_bucket()

    print("Uploaded new state to GCP")


if __name__ == "__main__":
    main()
