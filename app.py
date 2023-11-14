import datetime
import decimal
import json
import multiprocessing
import os

import pandas
import plotly.express
import streamlit

import src.constants
import src.histogram
import src.main_chart
import src.swap_liquidity
import update_data


def main():
    streamlit.title("DeRisk")

    (
        zklend_main_chart_data,
        zklend_histogram_data,
        zklend_loans,
    ) = src.helpers.load_data(protocol='zkLend')
    (
        hashstack_main_chart_data,
        hashstack_histogram_data,
        hashstack_loans,
    ) = src.helpers.load_data(protocol='Hashstack')
    (
        nostra_main_chart_data,
        nostra_histogram_data,
        nostra_loans,
    ) = src.helpers.load_data(protocol='Nostra')
    (
        nostra_uncapped_main_chart_data,
        nostra_uncapped_histogram_data,
        nostra_uncapped_loans,
    ) = src.helpers.load_data(protocol='Nostra uncapped')

    col1, _ = streamlit.columns([1, 3])
    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            options=["zkLend", "Hashstack", "Nostra", "Nostra uncapped"],
            default=["zkLend", "Hashstack", "Nostra", "Nostra uncapped"],
        )
        current_pair = streamlit.selectbox(
            label="Select collateral-loan pair:",
            options=src.constants.PAIRS,
            index=0,
        )

    data = pandas.DataFrame()
    loans = pandas.DataFrame()
    protocol_data_mapping = {
        'zkLend': zklend_main_chart_data[current_pair],
        'Hashstack': hashstack_main_chart_data[current_pair],
        'Nostra': nostra_main_chart_data[current_pair],
        'Nostra uncapped': nostra_uncapped_main_chart_data[current_pair],
    }
    protocol_loans_mapping = {
        'zkLend': zklend_loans,
        'Hashstack': hashstack_loans,
        'Nostra': nostra_loans,
        'Nostra uncapped': nostra_uncapped_loans,
    }
    for protocol in protocols:
        protocol_data = protocol_data_mapping[protocol]
        protocol_loans = protocol_loans_mapping[protocol]
        if data.empty:
            data = protocol_data
        else:
            data["liquidable_debt"] += protocol_data["liquidable_debt"]
            data["liquidable_debt_at_interval"] += protocol_data["liquidable_debt_at_interval"]
        if loans.empty:
            loans = protocol_loans
        else:
            loans = pandas.concat([loans, protocol_loans])

    # Plot the liquidable debt against the available supply.
    collateral_token, debt_token = current_pair.split("-")
    figure = src.main_chart.get_main_chart_figure(
        data=data.astype(float),
        collateral_token=collateral_token,
        debt_token=debt_token,
    )
    streamlit.plotly_chart(figure_or_data=figure, use_container_width=True)

    collateral_token_price = src.swap_liquidity.Prices().prices[collateral_token]
    example_row = data[
        data['collateral_token_price'] > decimal.Decimal("0.5") * collateral_token_price
    ].sort_values('collateral_token_price').iloc[0]

    def _get_risk_level(debt_to_supply_ratio: float) -> str:
        if debt_to_supply_ratio < 0.2:
            return 'low'
        elif debt_to_supply_ratio < 0.4:
            return 'medium'
        elif debt_to_supply_ratio < 0.6:
            'high'
        return 'very high'

    debt_to_supply_ratio = example_row['liquidable_debt_at_interval'] / example_row['debt_token_supply']
    streamlit.subheader(
        f":warning: At price of {int(example_row['collateral_token_price']):,}, the risk of acquiring bad debt for "
        f"lending protocols is {_get_risk_level(debt_to_supply_ratio)}."
    )    
    streamlit.write(
        f"The ratio of liquidated debt to available supply is {round(debt_to_supply_ratio * 100)}%.Debt worth of "
        f"{int(example_row['liquidable_debt_at_interval']):,} USD will be liquidated while the AMM swaps capacity "
        f"will be {int(example_row['debt_token_supply']):,} USD."
    )

    streamlit.header("Loans with low health factor")
    col1, _ = streamlit.columns([1, 3])
    with col1:
        debt_usd_lower_bound, debt_usd_upper_bound = streamlit.slider(
            label="Select range of USD borrowings",
            min_value=0,
            max_value=int(loans["Debt (USD)"].max()),
            value=(0, int(loans["Debt (USD)"].max())),
        )
    streamlit.dataframe(
        loans[
            (loans["Health factor"] > 0)  # TODO: debug the negative HFs
            & loans["Debt (USD)"].between(debt_usd_lower_bound, debt_usd_upper_bound)
        ].sort_values("Health factor").iloc[:20],
        use_container_width=True,
    )

    streamlit.header("Comparison of lending protocols")
    streamlit.dataframe(pandas.read_csv("data/general_stats.csv", compression="gzip"))
    streamlit.dataframe(pandas.read_csv("data/utilization_stats.csv", compression="gzip"))
    supply_stats = pandas.read_csv("data/supply_stats.csv", compression="gzip")
    collateral_stats = pandas.read_csv("data/collateral_stats.csv", compression="gzip")
    debt_stats = pandas.read_csv("data/debt_stats.csv", compression="gzip")

    columns = streamlit.columns(6)
    for column, token in zip(columns, src.constants.TOKEN_DECIMAL_FACTORS.keys()):
        with column:
            figure = plotly.express.pie(
                collateral_stats,
                values=f'{token} collateral',
                names='Protocol',
                title=f'{token} collateral',
                color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
            )
            streamlit.plotly_chart(figure, True)
            figure = plotly.express.pie(
                debt_stats,
                values=f'{token} debt',
                names='Protocol',
                title=f'{token} debt',
                color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
            )
            streamlit.plotly_chart(figure, True)
            figure = plotly.express.pie(
                supply_stats,
                values=f'{token} supply',
                names='Protocol',
                title=f'{token} supply',
                color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
            )
            streamlit.plotly_chart(figure, True)

    streamlit.header("Loan size distribution")
    src.histogram.visualization(protocols)

    with open("zklend_data/last_update.json", "r") as f:
        last_update = json.load(f)
        last_updated = last_update["timestamp"]
        last_block_number = last_update["block_number"]
    date_str = datetime.datetime.utcfromtimestamp(int(last_updated))
    streamlit.write(f"Last updated {date_str} UTC, last block: {last_block_number}")


if __name__ == "__main__":
    streamlit.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    if os.environ.get("UPDATE_RUNNING") is None:
        os.environ["UPDATE_RUNNING"] = "True"
        # TODO: Switch to logging.
        print("Spawning the updating process.", flush=True)
        update_data_process = multiprocessing.Process(
            target=update_data.update_data_continuously, daemon=True
        )
        update_data_process.start()
    main()
