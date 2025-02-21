import pandas as pd
import pytest

from apps.dashboard_app.main_chart_figure import get_user_history
from data_conector import DataConnector

@pytest.fixture
def data_connector():
    connector = DataConnector()
    return connector

def test_fetch_data_from_csv(data_connector):

    file_path = 'apps/dashboard_app/data/data.csv'
    expected_columns = ['User','Collateral (USD)','Risk-adjusted collateral (USD)','Debt (USD)','Health factor','Standardized health factor','Collateral','Debt']

    df = data_connector.fetch_data_from_csv(file_path)

    assert isinstance(df, pd.DataFrame)
    assert df.columns.tolist() == expected_columns


def test_get_user_history(data_connector):

    user_id = '0x04aa93bc6f2d76e90474cc82914c219bcdcfb91511225e08b6a284a62e8ac6e1'
    expected_result = pd.DataFrame({
        'Transaction': [1]
        CommonValues.collateral_usd.value: [54.685892],
        CommonValues.debt_usd.value:: [11.343674]
    })

    result = get_user_history(data_connector, user_id)

    pd.testing.assert_frame_equal(result, expected_result)


