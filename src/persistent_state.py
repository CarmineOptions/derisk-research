import logging
import pickle

import requests

import src.helpers
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
            logging.info(f"Failed to unpickle the data: {e}")
            return src.zklend.ZkLendState()
    else:
        logging.info(f"Failed to download file. Status code: {response.status_code}")
        return src.zklend.ZkLendState()


def upload_state_as_pickle(state):
    with open(PERSISTENT_STATE_FILENAME, "wb") as out_file:
        pickle.dump(state, out_file)
    src.helpers.upload_file_to_bucket(
        source_path=PERSISTENT_STATE_FILENAME,
        target_path=PERSISTENT_STATE_FILENAME,
    )


def update_persistent_state_manually():
    zklend_events = src.zklend.get_events()

    zklend_state = src.zklend.ZkLendState()
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    with open(PERSISTENT_STATE_FILENAME, "wb") as file:
        pickle.dump(zklend_state, file)

    src.helpers.upload_file_to_bucket(
        source_path=PERSISTENT_STATE_FILENAME,
        target_path=PERSISTENT_STATE_FILENAME,
    )
    # TODO: Remove persistent state?
    logging.info(
        f"Created and saved a new persistent state under the latest block = {zklend_state.last_block_number}."
    )