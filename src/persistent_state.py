import logging
import os
import pickle
import sys
import google.cloud.storage
import requests

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
    upload_file_to_bucket(PERSISTENT_STATE_FILENAME, PERSISTENT_STATE_FILENAME)


def upload_file_to_bucket(source, target):
    bucket_name = "derisk-persistent-state"

    # Initialize the Google Cloud Storage client with the credentials
    storage_client = google.cloud.storage.Client.from_service_account_json(
        os.getenv("CREDENTIALS_PATH"))

    # Get the target bucket
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket
    blob = bucket.blob(target)
    blob.upload_from_filename(source)
    logging.info(f"File {source} uploaded to gs://{bucket_name}/{target}")