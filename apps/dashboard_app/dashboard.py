"""
This script loads data and runs the dashboard.
"""

import logging

from charts.main import Dashboard
from helpers.load_data import DashboardDataHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    dashboard_data_handler = DashboardDataHandler()
    (
        zklend_state,
        general_stats,
        supply_stats,
        collateral_stats,
        debt_stats,
        utilization_stats,
    ) = dashboard_data_handler.load_data()

    dashboard = Dashboard(zklend_state)
    dashboard.run()
