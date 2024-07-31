import logging

import update_data



if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	update_data.update_data_continuously()