from typing import Any
import logging
import os
import pickle

import requests

import src.helpers
import src.zklend



PERSISTENT_STATE_FILENAME = "persistent-state.pckl"
LAST_UPDATE_FILENAME = "last_update.json"



def load_pickle(path: str) -> src.zklend.ZkLendState:
    # TODO: generalize to last_update.json!
    # TODO: generalize to every protocol
    # TODO: use https://stackoverflow.com/a/58709164 instead?
    response = requests.get(
        f"https://storage.googleapis.com/{src.helpers.GS_BUCKET_NAME}/{path}"
    )
    if response.status_code == 200:
        try:
            state = pickle.loads(response.content)
            return state
        except pickle.UnpicklingError as e:
            logging.info(f"Failed to unpickle the data: {e}.")
            return src.zklend.ZkLendState()
    else:
        logging.info(f"Failed to load the file. Status code: {response.status_code}.")
        return src.zklend.ZkLendState()


def upload_object_as_pickle(object: Any, path: str):
    with open(path, "wb") as out_file:
        pickle.dump(object, out_file)
    src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def update_persistent_state_manually():
    zklend_events = src.zklend.zklend_get_events()

    zklend_state = src.zklend.ZkLendState()
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    with open(PERSISTENT_STATE_FILENAME, "wb") as file:
        pickle.dump(zklend_state, file)
    src.helpers.upload_file_to_bucket(
        source_path=PERSISTENT_STATE_FILENAME,
        target_path=PERSISTENT_STATE_FILENAME,
    )
    os.remove(PERSISTENT_STATE_FILENAME)
    
    logging.info(
        f"Created and saved a new persistent state under the latest block = {zklend_state.last_block_number}."
    )