import logging
from dashboard_app.charts import Dashboard
from dashboard_app.helpers.load_data import DashboardDataHandler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dashboard_data_handler = DashboardDataHandler()
    dashboard_data_handler.load_data()

    # dashboard = Dashboard()
    # dashboard.run()
