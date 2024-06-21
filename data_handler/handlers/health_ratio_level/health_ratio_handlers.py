from db.crud import DBConnector
from db.models import HealthRatioLevel

from handlers.state import State, LoanEntity


class HealthRatioHandler:
    """
    A handler that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :cvar CONNECTOR: A DB connection object.
    """
    CONNECTOR = DBConnector()

    def __init__(
            self,
            loan_state_class: State,
            loan_entity_class: LoanEntity,
    ):
        self.state_class = loan_state_class
        self.loan_entity_class = loan_entity_class
