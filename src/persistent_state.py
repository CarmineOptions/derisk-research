from typing import Any
import logging
import os

import dill
import requests

import src.helpers
import src.zklend



PERSISTENT_STATE_FILENAME = "persistent-state.pkl"
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
            state = dill.loads(response.content)
            # TODO: When loanding the pickled state, `'': decimal.Decimal('0')`` is added to every Portfolio. Remove these items.
            if PERSISTENT_STATE_FILENAME in path:
                for loan_entity in state.loan_entities.values():
                    if '' in loan_entity.collateral:
                        del loan_entity.collateral['']
                    if ''  in loan_entity.debt:
                        del loan_entity.debt['']
            return state
        except dill.UnpicklingError as e:
            logging.info(f"Failed to unpickle the data: {e}.")
            return src.zklend.ZkLendState()
    else:
        logging.info(f"Failed to load the file. Status code: {response.status_code}.")
        return src.zklend.ZkLendState()


def upload_object_as_pickle(object: Any, path: str):
    with open(path, "wb") as out_file:
        dill.dump(object, out_file)
    src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def update_persistent_state_manually():
    zklend_events = src.zklend.zklend_get_events()

    zklend_state = src.zklend.ZkLendState()
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    upload_object_as_pickle(object = zklend_state, path = PERSISTENT_STATE_FILENAME)
    
    logging.info(
        f"Created and saved a new persistent state under the latest block = {zklend_state.last_block_number}."
    )