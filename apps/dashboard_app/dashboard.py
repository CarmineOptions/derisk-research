"""
This script loads data and runs the dashboard.
"""

import logging
import asyncio
from dashboard_app.charts.utils import  streamlit_dev_fill_with_test_data
from charts.main import Dashboard
from helpers.load_data import DashboardDataHandler
from streamlit_autorefresh import st_autorefresh
from shared.constants import CRONTAB_TIME
logger = logging.getLogger(__name__)
ONE_MINUTE_IN_MILISECONDS = 60000
REFRESH_TIME = ONE_MINUTE_IN_MILISECONDS * int(CRONTAB_TIME)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    streamlit_dev_fill_with_test_data()

    dashboard = Dashboard() # (`st.set_page_config` in `Dashboard` must be called once)
    # Set up autorefresh data config
    st_autorefresh(interval=REFRESH_TIME, key="datarefresh")

    dashboard_data_handler =  asyncio.run(DashboardDataHandler.create())
    (
        dashboard.state,
        dashboard.general_stats,
        dashboard.supply_stats,
        dashboard.collateral_stats,
        dashboard.debt_stats,
        dashboard.utilization_stats,
    ) = dashboard_data_handler.load_data()

    dashboard.run()