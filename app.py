import datetime
import decimal
import multiprocessing
import os

import pandas
import plotly.express
import streamlit

import src.constants
import src.hashstack
import src.histogram
import update_data


def main():
    streamlit.title("DeRisk")

    # TODO: rename: data -> zklend_data
    (
        data,
        zklend_loans,
        last_updated,
        last_block_number,
    ) = src.zklend.load_data()
    (
        hashstack_data,
        hashstack_histogram_data,
        hashstack_loans,
    ) = src.hashstack.load_data()
    (
        nostra_data,
        nostra_histogram_data,
        nostra_loans,
    ) = src.nostra.load_data()

    col1, _ = streamlit.columns([1, 3])
    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            options=["zkLend", "Hashstack", "Nostra"],
            default=["zkLend", "Hashstack", "Nostra"],
        )
        current_pair = streamlit.selectbox(
            label="Select collateral-loan pair:",
            options=src.constants.PAIRS,
            index=0,
        )

    # TODO: refactor this mess
    if protocols == ["zkLend"]:
        data[current_pair] = data[current_pair]
        loans = zklend_loans
    elif protocols == ["Hashstack"]:
        data[current_pair] = hashstack_data[current_pair]
        loans = hashstack_loans
    elif protocols == ["Nostra"]:
        data[current_pair] = nostra_data[current_pair]
        loans = nostra_loans
    elif set(protocols) == {"zkLend", "Hashstack"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += hashstack_data[
            current_pair
        ]["max_borrowings_to_be_liquidated"]
        data[current_pair][
            "max_borrowings_to_be_liquidated_at_interval"
        ] += hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        loans = pandas.concat([zklend_loans, hashstack_loans])
    elif set(protocols) == {"zkLend", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += nostra_data[
            current_pair
        ]["max_borrowings_to_be_liquidated"]
        data[current_pair][
            "max_borrowings_to_be_liquidated_at_interval"
        ] += nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        loans = pandas.concat([zklend_loans, nostra_loans])
    elif set(protocols) == {"Hashstack", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] = (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated"]
        )
        data[current_pair]["max_borrowings_to_be_liquidated_at_interval"] = (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        )
        loans = pandas.concat([hashstack_loans, nostra_loans])
    elif set(protocols) == {"zkLend", "Hashstack", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated"]
        )
        data[current_pair]["max_borrowings_to_be_liquidated_at_interval"] += (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        )
        loans = pandas.concat([zklend_loans, hashstack_loans, nostra_loans])

    [col, bor] = current_pair.split("-")

    color_map = {
        "max_borrowings_to_be_liquidated_at_interval": "#ECD662",
        "amm_borrowings_token_supply": "#4CA7D0",
    }

    figure = plotly.express.bar(
        data[current_pair].astype(float),
        x="collateral_token_price",
        y=[
            "max_borrowings_to_be_liquidated_at_interval",
            "amm_borrowings_token_supply",
        ],
        title=f"Potentially liquidatable amounts of {bor} loans and the corresponding supply of {col}",
        barmode="overlay",
        opacity=0.65,
        color_discrete_map=color_map,
    )
    figure.update_traces(hovertemplate=("<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"))
    figure.update_traces(
        selector=dict(name="max_borrowings_to_be_liquidated_at_interval"),
        name="Liquidable",
    )
    figure.update_traces(
        selector=dict(name="amm_borrowings_token_supply"), name="AMM Supply"
    )
    figure.update_xaxes(title_text=f"{col} price")
    figure.update_yaxes(title_text="Volume")
    collateral_token_price = src.swap_liquidity.Prices().prices[col]
    figure.add_vline(
        x=collateral_token_price,
        line_width=2,
        line_dash="dash",
        line_color="black",
    )
    figure.add_vrect(
        x0=decimal.Decimal("0.9") * collateral_token_price,
        x1=decimal.Decimal("1.1") * collateral_token_price,
        annotation_text="Current price +- 10%",
        annotation_font_size=11,
        annotation_position="top left",
        fillcolor="gray",
        opacity=0.25,
        line_width=2,
    )
    streamlit.plotly_chart(figure, True)
    example_row = data[current_pair][
        data[current_pair]['collateral_token_price'] > decimal.Decimal("0.5") * collateral_token_price
    ].sort_values('collateral_token_price').iloc[0]

    def _get_risk_level(debt_to_supply_ratio: float) -> str:
        if debt_to_supply_ratio < 0.2:
            return 'low'
        elif debt_to_supply_ratio < 0.4:
            return 'medium'
        elif debt_to_supply_ratio < 0.6:
            'high'
        return 'very high'

    debt_to_supply_ratio = example_row['max_borrowings_to_be_liquidated_at_interval'] / example_row['amm_borrowings_token_supply']
    streamlit.subheader(
        f":warning: At price of {int(example_row['collateral_token_price']):,}, the risk of acquiring bad debt for lending protocols is "
        f"{_get_risk_level(debt_to_supply_ratio)}."
    )    
    streamlit.write(
        f"The ratio of liquidated debt to available supply is {round(debt_to_supply_ratio * 100)}%.Debt worth of "
        f"{int(example_row['max_borrowings_to_be_liquidated_at_interval']):,} USD will be liquidated while the AMM swaps capacity will "
        f"be {int(example_row['amm_borrowings_token_supply']):,} USD."
    )

    streamlit.header("Loans with low health factor")
    col1, _ = streamlit.columns([1, 3])
    with col1:
        debt_usd_lower_bound, debt_usd_upper_bound = streamlit.slider(
            label="Select range of USD borrowings",
            min_value=0,
            max_value=int(loans["Borrowing in USD"].max()),
            value=(0, int(loans["Borrowing in USD"].max())),
        )
    streamlit.dataframe(
        loans[
            (loans["Health factor"] > 0)  # TODO: debug the negative HFs
            & loans["Borrowing in USD"].between(debt_usd_lower_bound, debt_usd_upper_bound)
        ].sort_values("Health factor").iloc[:20],
        use_container_width=True,
    )

    streamlit.header("Comparison of lending protocols")
    streamlit.dataframe(pandas.read_csv("general_stats.csv", compression="gzip"))
    streamlit.dataframe(pandas.read_csv("utilization_stats.csv", compression="gzip"))
    supply_stats = pandas.read_csv("supply_stats.csv", compression="gzip")
    collateral_stats = pandas.read_csv("collateral_stats.csv", compression="gzip")
    debt_stats = pandas.read_csv("debt_stats.csv", compression="gzip")
    col1, col2, col3, col4, col5, col6 = streamlit.columns(6)
    with col1:
        figure = plotly.express.pie(
            collateral_stats,
            values='ETH collateral',
            names='Protocol',
            title="ETH collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='ETH debt',
            names='Protocol',
            title="ETH debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='ETH supply',
            names='Protocol',
            title="ETH supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    with col2:
        figure = plotly.express.pie(
            collateral_stats,
            values='wBTC collateral',
            names='Protocol',
            title="wBTC collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='wBTC debt',
            names='Protocol',
            title="wBTC debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='wBTC supply',
            names='Protocol',
            title="wBTC supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    with col3:
        figure = plotly.express.pie(
            collateral_stats,
            values='USDC collateral',
            names='Protocol',
            title="USDC collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='USDC debt',
            names='Protocol',
            title="USDC debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='USDC supply',
            names='Protocol',
            title="USDC supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    with col4:
        figure = plotly.express.pie(
            collateral_stats,
            values='DAI collateral',
            names='Protocol',
            title="DAI collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='DAI debt',
            names='Protocol',
            title="DAI debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='DAI supply',
            names='Protocol',
            title="DAI supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    with col5:
        figure = plotly.express.pie(
            collateral_stats,
            values='USDT collateral',
            names='Protocol',
            title="USDT collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='USDT debt',
            names='Protocol',
            title="USDT debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='USDT supply',
            names='Protocol',
            title="USDT supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    with col6:
        figure = plotly.express.pie(
            collateral_stats,
            values='wstETH collateral',
            names='Protocol',
            title="wstETH collateral",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            debt_stats,
            values='wstETH debt',
            names='Protocol',
            title="wstETH debt",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)
        figure = plotly.express.pie(
            supply_stats,
            values='wstETH supply',
            names='Protocol',
            title="USDT supply",
            color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
        )
        streamlit.plotly_chart(figure, True)
    streamlit.header("Loan size distribution")
    src.histogram.visualization(protocols)

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
