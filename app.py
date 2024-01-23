import datetime
import decimal
import json
import logging
import multiprocessing
import os

import pandas
import plotly.express
import streamlit

import src.helpers
import src.histogram
import src.main_chart
import src.persistent_state
import src.settings
import src.swap_amm
import update_data



logging.basicConfig(level=logging.INFO)



def main():
    streamlit.title("DeRisk")

    (
        zklend_main_chart_data,
        zklend_histogram_data,
        zklend_loans_data,
    ) = src.helpers.load_data(protocol='zkLend')
    (
        hashstack_main_chart_data,
        hashstack_histogram_data,
        hashstack_loans_data,
    ) = src.helpers.load_data(protocol='Hashstack')
    (
        nostra_alpha_main_chart_data,
        nostra_alpha_histogram_data,
        nostra_alpha_loans_data,
    ) = src.helpers.load_data(protocol='Nostra Alpha')
    (
        nostra_mainnet_main_chart_data,
        nostra_mainnet_histogram_data,
        nostra_mainnet_loans_data,
    ) = src.helpers.load_data(protocol='Nostra Mainnet')

    col1, _ = streamlit.columns([1, 3])
    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            options=["zkLend", "Hashstack", "Nostra Alpha", "Nostra Mainnet"],
            default=["zkLend", "Hashstack", "Nostra Alpha", "Nostra Mainnet"],
        )
        current_pair = streamlit.selectbox(
            label="Select collateral-loan pair:",
            options=src.settings.PAIRS,
            index=0,
        )

    main_chart_data = pandas.DataFrame()
    histogram_data = pandas.DataFrame()
    loans_data = pandas.DataFrame()
    protocol_main_chart_data_mapping = {
        'zkLend': zklend_main_chart_data[current_pair],
        'Hashstack': hashstack_main_chart_data[current_pair],
        'Nostra Alpha': nostra_alpha_main_chart_data[current_pair],
        'Nostra Mainnet': nostra_mainnet_main_chart_data[current_pair],
    }
    protocol_histogram_data_mapping = {
        'zkLend': zklend_histogram_data,
        'Hashstack': hashstack_histogram_data,
        'Nostra Alpha': nostra_alpha_histogram_data,
        'Nostra Mainnet': nostra_mainnet_histogram_data,
    }
    protocol_loans_data_mapping = {
        'zkLend': zklend_loans_data,
        'Hashstack': hashstack_loans_data,
        'Nostra Alpha': nostra_alpha_loans_data,
        'Nostra Mainnet': nostra_mainnet_loans_data,
    }
    for protocol in protocols:
        protocol_main_chart_data = protocol_main_chart_data_mapping[protocol]
        protocol_histogram_data = protocol_histogram_data_mapping[protocol]
        protocol_loans_data = protocol_loans_data_mapping[protocol]
        if main_chart_data.empty:
            main_chart_data = protocol_main_chart_data
        else:
            main_chart_data["liquidable_debt"] += protocol_main_chart_data["liquidable_debt"]
            main_chart_data["liquidable_debt_at_interval"] += protocol_main_chart_data["liquidable_debt_at_interval"]
        if histogram_data.empty:
            histogram_data = protocol_histogram_data
        else:
            histogram_data = pandas.concat([histogram_data, protocol_histogram_data])
        if loans_data.empty:
            loans_data = protocol_loans_data
        else:
            loans_data = pandas.concat([loans_data, protocol_loans_data])

    # Plot the liquidable debt against the available supply.
    collateral_token, debt_token = current_pair.split("-")
    figure = src.main_chart.get_main_chart_figure(
        data=main_chart_data.astype(float),
        collateral_token=collateral_token,
        debt_token=debt_token,
    )
    streamlit.plotly_chart(figure_or_data=figure, use_container_width=True)

    main_chart_data['debt_to_supply_ratio'] = (
        main_chart_data['liquidable_debt_at_interval'] / main_chart_data['debt_token_supply']
    )
    example_row = main_chart_data[
        main_chart_data['debt_to_supply_ratio'] > 0.75
    ].sort_values('collateral_token_price').iloc[-1]

    if not example_row.empty:
        def _get_risk_level(debt_to_supply_ratio: float) -> str:
            if debt_to_supply_ratio < 0.2:
                return 'low'
            elif debt_to_supply_ratio < 0.4:
                return 'medium'
            elif debt_to_supply_ratio < 0.6:
                'high'
            return 'very high'

        streamlit.subheader(
            f":warning: At price of {int(example_row['collateral_token_price']):,}, the risk of acquiring bad debt for "
            f"lending protocols is {_get_risk_level(example_row['debt_to_supply_ratio'])}."
        )    
        streamlit.write(
            f"The ratio of liquidated debt to available supply is {round(example_row['debt_to_supply_ratio'] * 100)}%.Debt"
            f" worth of {int(example_row['liquidable_debt_at_interval']):,} USD will be liquidated while the AMM swaps "
            f"capacity will be {int(example_row['debt_token_supply']):,} USD."
        )

    streamlit.header("Loans with low health factor")
    col1, _ = streamlit.columns([1, 3])
    with col1:
        debt_usd_lower_bound, debt_usd_upper_bound = streamlit.slider(
            label="Select range of USD borrowings",
            min_value=0,
            max_value=int(loans_data["Debt (USD)"].max()),
            value=(0, int(loans_data["Debt (USD)"].max())),
        )
    streamlit.dataframe(
        loans_data[
            (loans_data["Health factor"] > 0)  # TODO: debug the negative HFs
            & loans_data["Debt (USD)"].between(debt_usd_lower_bound, debt_usd_upper_bound)
        ].sort_values("Health factor").iloc[:20],
        use_container_width=True,
    )

    streamlit.header("Comparison of lending protocols")
    streamlit.dataframe(pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/data/general_stats.parquet"))
    streamlit.dataframe(pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/data/utilization_stats.parquet"))
    supply_stats = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/data/supply_stats.parquet")
    collateral_stats = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/data/collateral_stats.parquet")
    debt_stats = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/data/debt_stats.parquet")

    columns = streamlit.columns(6)
    for column, token in zip(columns, src.settings.TOKEN_SETTINGS.keys()):
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
    src.histogram.visualization(data=histogram_data)

    last_update = src.persistent_state.load_pickle(path=src.persistent_state.LAST_UPDATE_FILENAME)
    last_timestamp = last_update["timestamp"]
    last_block_number = last_update["block_number"]
    date_str = datetime.datetime.utcfromtimestamp(int(last_timestamp))
    streamlit.write(f"Last updated {date_str} UTC, last block: {last_block_number}.")


if __name__ == "__main__":
    streamlit.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    if os.environ.get("UPDATE_RUNNING") is None:
        os.environ["UPDATE_RUNNING"] = "True"
        logging.info("Spawning the updating process.")
        update_data_process = multiprocessing.Process(
            target=update_data.update_data_continuously, daemon=True
        )
        update_data_process.start()
    main()
