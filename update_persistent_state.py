import logging

import src.persistent_state



logging.basicConfig(level=logging.INFO)



if __name__ == "__main__":
    src.persistent_state.update_persistent_state_manually()