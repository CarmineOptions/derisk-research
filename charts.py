import logging
import pandas
import plotly
import numpy
import src
import app
from app import ZKLEND, NOSTRA_ALPHA, NOSTRA_MAINNET


def get_charts_data(
    main_chart_data, loans_data, protocols, collateral_token, debt_token
):
    for protocol in protocols:
        protocol_main_chart_data = get_protocol_main_data()[protocol]
        if protocol_main_chart_data is None or protocol_main_chart_data.empty:
            logging.warning(
                f"No data for pair {debt_token} - {collateral_token} from {protocol}"
            )
            continue

        protocol_loans_data = get_protocol_loans_data()[protocol]

        if main_chart_data.empty:
            main_chart_data = protocol_main_chart_data
            main_chart_data[f"liquidable_debt_{protocol}"] = protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data[f"liquidable_debt_at_interval_{protocol}"] = (
                protocol_main_chart_data["liquidable_debt_at_interval"]
            )
        else:
            main_chart_data["liquidable_debt"] += protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data["liquidable_debt_at_interval"] += protocol_main_chart_data[
                "liquidable_debt_at_interval"
            ]
            main_chart_data[f"liquidable_debt_{protocol}"] = protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data[f"liquidable_debt_at_interval_{protocol}"] = (
                protocol_main_chart_data["liquidable_debt_at_interval"]
            )

        if loans_data.empty:
            loans_data = protocol_loans_data
        else:
            loans_data = pandas.concat([loans_data, protocol_loans_data])

        return main_chart_data, loans_data


def get_protocol_main_data(
    zklend, nostra_alpha, nostra_mainnet, current_pair, stable_coin_pair
):
    protocol_main_chart_data_mapping = (
        {
            ZKLEND: app.create_stablecoin_bundle(zklend)[current_pair],
            # 'Hashstack V0': hashstack_v0_main_chart_data[current_pair],
            # 'Hashstack V1': hashstack_v1_main_chart_data[current_pair],
            NOSTRA_ALPHA: app.create_stablecoin_bundle(nostra_alpha)[current_pair],
            NOSTRA_MAINNET: app.create_stablecoin_bundle(nostra_mainnet)[current_pair],
        }
        if current_pair == stable_coin_pair
        else {
            ZKLEND: zklend[current_pair],
            # 'Hashstack V0': hashstack_v0_main_chart_data[current_pair],
            # 'Hashstack V1': hashstack_v1_main_chart_data[current_pair],
            NOSTRA_ALPHA: nostra_alpha[current_pair],
            NOSTRA_MAINNET: nostra_mainnet[current_pair],
        }
    )
    return protocol_main_chart_data_mapping


def get_protocol_loans_data(zklend, nostra_alpha, nostra_mainnet):
    protocol_loans_data_mapping = {
        ZKLEND: zklend,
        # 'Hashstack V0': hashstack_v0_loans_data,
        # 'Hashstack V1': hashstack_v1_loans_data,
        NOSTRA_ALPHA: nostra_alpha,
        NOSTRA_MAINNET: nostra_mainnet,
    }
    return protocol_loans_data_mapping


def noname_func(main_chart_data, current_pair, stable_coin_pair, collateral_token):
    if current_pair == stable_coin_pair:
        for stable_coin in src.settings.DEBT_TOKENS[:-1]:
            debt_token = stable_coin
            main_chart_data, collateral_token_price = app.process_liquidity(
                main_chart_data, collateral_token, debt_token
            )
    else:
        main_chart_data, collateral_token_price = app.process_liquidity(
            main_chart_data, collateral_token, debt_token
        )
    return main_chart_data, collateral_token_price


def get_usd_debt_boundaries(col1, streamlit, loans_data):
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
            & loans_data["Debt (USD)"].between(
                debt_usd_lower_bound, debt_usd_upper_bound
            )
        ]
        .sort_values("Health factor")
        .iloc[:20],
        use_container_width=True,
    )


def lottery(col1, streamlit, loans_data):
    with col1:
        user = streamlit.text_input("User")
        protocol = streamlit.text_input("Protocol")

        users_and_protocols_with_debt = list(
            loans_data.loc[
                loans_data["Debt (USD)"] > 0,
                ["User", "Protocol"],
            ].itertuples(index=False, name=None)
        )

        random_user, random_protocol = users_and_protocols_with_debt[
            numpy.random.randint(len(users_and_protocols_with_debt))
        ]

        if not user:
            streamlit.write(f"Selected random user = {random_user}.")
            user = random_user
        if not protocol:
            streamlit.write(f"Selected random protocol = {random_protocol}.")
            protocol = random_protocol

    return user, protocol


def get_pie_chart(col2, col3, streamlit, collateral_usd_amounts, debt_usd_amounts):
    with col2:
        figure = plotly.express.pie(
            collateral_usd_amounts,
            values="amount_usd",
            names="token",
            title="Collateral (USD)",
            color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
        )
        streamlit.plotly_chart(figure, True)

    with col3:
        figure = plotly.express.pie(
            debt_usd_amounts,
            values="amount_usd",
            names="token",
            title="Debt (USD)",
            color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
        )
        streamlit.plotly_chart(figure, True)


def get_parquets():
    general_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/general_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    supply_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/supply_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    collateral_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/collateral_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    debt_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/debt_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    general_stats["TVL (USD)"] = (
        supply_stats["Total supply (USD)"] - general_stats["Total debt (USD)"]
    )
    return general_stats, supply_stats, collateral_stats, debt_stats


def get_multi_pie_chart(
    streamlit, columns, tokens, collateral_stats, debt_stats, supply_stats
):
    for column, token_1, token_2 in zip(columns, tokens[:4], tokens[4:]):
        with column:
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    collateral_stats.reset_index(),
                    values=f"{token} collateral",
                    names="Protocol",
                    title=f"{token} collateral",
                    color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
                )
                streamlit.plotly_chart(figure, True)

            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    debt_stats.reset_index(),
                    values=f"{token} debt",
                    names="Protocol",
                    title=f"{token} debt",
                    color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
                )
                streamlit.plotly_chart(figure, True)

            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    supply_stats.reset_index(),
                    values=f"{token} supply",
                    names="Protocol",
                    title=f"{token} supply",
                    color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
                )
                streamlit.plotly_chart(figure, True)
