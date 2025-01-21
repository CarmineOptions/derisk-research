"""
This script loads data and runs the dashboard.
"""

import logging

from data_handler.handlers.loan_states.zklend.events import ZkLendState

from charts.main import Dashboard
from helpers.load_data import DashboardDataHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dashboard_data_handler = DashboardDataHandler()
    dashboard_data_handler.load_data()
    zklend_state = ZkLendState()

    dashboard = Dashboard(zklend_state)
    dashboard.run()
