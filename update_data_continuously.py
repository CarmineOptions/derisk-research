import logging

import update_data



if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	update_data.update_data_continuously()
	# TODO
    # zklend_state = src.persistent_state.load_pickle(path=src.persistent_state.PERSISTENT_STATE_FILENAME)
    # update_data(zklend_state)