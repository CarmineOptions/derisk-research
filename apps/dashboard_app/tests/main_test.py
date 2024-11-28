import pytest
from unittest.mock import patch, MagicMock
from dashboard_app.charts import Dashboard

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit methods."""
    with patch("dashboard_app.charts.main.st") as mock_st:
        yield mock_st

@pytest.fixture
def mock_dependencies():
    """Mock external utility functions."""
    with patch("dashboard_app.charts.utils.get_protocol_data_mappings", return_value=({}, {})):
        with patch("dashboard_app.charts.utils.transform_loans_data", return_value={}):
            with patch("dashboard_app.charts.utils.transform_main_chart_data", return_value=[]):
                with patch("dashboard_app.charts.utils.process_liquidity", return_value=([], 0)):
                    with patch("dashboard_app.charts.main_chart_figure.get_main_chart_figure", return_value=MagicMock()):
                        yield

def test_dashboard_run(mock_streamlit, mock_dependencies):
    """Test the full execution of the dashboard run method."""
    mock_state = MagicMock()
    dashboard = Dashboard(mock_state)

    # Mock internal methods
    with patch.object(dashboard, "load_sidebar") as mock_sidebar, patch.object(
        dashboard, "load_main_chart"
    ) as mock_main_chart:
        dashboard.run()

        mock_sidebar.assert_called_once()
        mock_main_chart.assert_called_once()
