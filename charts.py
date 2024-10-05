import logging
import pandas as pd
import plotly
import numpy as np 
import streamlit
import src
import app
from app import ZKLEND, NOSTRA_ALPHA, NOSTRA_MAINNET


def get_charts_data(
    main_chart_data: pd.DataFrame,
    loans_data: pd.DataFrame,
    protocols: list[str],
    collateral_token: str,
    debt_token: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Combines the chart data and loan data for different protocols.

    Args:
        main_chart_data (pd.DataFrame): Dataframe for main chart data.
        loans_data (pd.DataFrame): Dataframe for loans data.
        protocols (list[str]): List of protocols to aggregate data from.
        collateral_token (str): The collateral token used.
        debt_token (str): The debt token used.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Updated main chart and loans data.
    """

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
            loans_data = pd.concat([loans_data, protocol_loans_data])

        return main_chart_data, loans_data


def get_protocol_main_mapped_chart_data(zklend: pd.DataFrame,
    nostra_alpha: pd.DataFrame,
    nostra_mainnet: pd.DataFrame,
    current_pair: str,
    stable_coin_pair: str
) -> dict[str, pd.DataFrame]:
    """
    Retrieves the main chart data for different protocols based on the current pair.

    Args:
        zklend (pd.DataFrame): Main chart data for the ZK Lend protocol.
        nostra_alpha (pd.DataFrame): Main chart data for the Nostra Alpha protocol.
        nostra_mainnet (pd.DataFrame): Main chart data for the Nostra Mainnet protocol.
        current_pair (str): The current pair of tokens being analyzed.
        stable_coin_pair (str): The stablecoin pair to compare with.

    Returns:
        dict[str, pd.DataFrame]: Mapping of protocols to their respective chart data.
    """

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


def get_protocol_loans_mapped_data(zklend: pd.DataFrame,
    nostra_alpha: pd.DataFrame,
    nostra_mainnet: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """
    Retrieves loans data for different protocols.
    Args:
        zklend (pd.DataFrame): Loans data for the ZK Lend protocol.
        nostra_alpha (pd.DataFrame): Loans data for the Nostra Alpha protocol.
        nostra_mainnet (pd.DataFrame): Loans data for the Nostra Mainnet protocol.

    Returns:
        dict[str, pd.DataFrame]: Mapping of protocols to their respective loans data.
    """

    protocol_loans_data_mapping = {
        ZKLEND: zklend,
        # 'Hashstack V0': hashstack_v0_loans_data,
        # 'Hashstack V1': hashstack_v1_loans_data,
        NOSTRA_ALPHA: nostra_alpha,
        NOSTRA_MAINNET: nostra_mainnet,
    }
    return protocol_loans_data_mapping


def noname_func(main_chart_data: pd.DataFrame,
    current_pair: str,
    stable_coin_pair: str,
    collateral_token: str
) -> tuple[pd.DataFrame, float]:
    """
    Processes liquidity and adjusts main chart data and collateral token price.

    Args:
        main_chart_data (pd.DataFrame): The main chart data to process.
        current_pair (str): The current pair of tokens being analyzed.
        stable_coin_pair (str): The stablecoin pair to compare with.
        collateral_token (str): The collateral token used.

    Returns:
        tuple[pd.DataFrame, float]: Updated main chart data and collateral token price.
    """

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


def get_usd_debt_boundaries(col1: list[streamlit.delta_generator.DeltaGenerator],
                            loans_data: pd.DataFrame) -> None:
    """
    Displays a slider to filter USD borrowings within a specific range and shows the results.

    Args:
        col1: Streamlit column object for layout.
        loans_data (pd.DataFrame): Dataframe containing loans information.
    """

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


def select_random_user_protocol(col1: list[streamlit.delta_generator.DeltaGenerator],  
                                loans_data: pd.DataFrame
) -> tuple[str, str]:
    """
    Randomly selects a user and protocol from the loans data, or accepts user input.

    Args:
        col1: Streamlit column object for layout.
        loans_data (pd.DataFrame): Dataframe containing loans information.

    Returns:
        tuple[str, str]: Selected or input user and protocol.
    """

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
            np.random.randint(len(users_and_protocols_with_debt))
        ]

        if not user:
            streamlit.write(f"Selected random user = {random_user}.")
            user = random_user
        if not protocol:
            streamlit.write(f"Selected random protocol = {random_protocol}.")
            protocol = random_protocol

    return user, protocol


def get_pie_chart(col2: list[streamlit.delta_generator.DeltaGenerator], 
                  col3: list[streamlit.delta_generator.DeltaGenerator],
                  collateral_usd_amounts: pd.DataFrame, 
                  debt_usd_amounts: pd.DataFrame
) -> None:
    """
    Displays pie charts for collateral and debt amounts in USD.

    Args:
        col2: Streamlit column object for collateral chart.
        col3: Streamlit column object for debt chart.
        collateral_usd_amounts (pd.DataFrame): Dataframe of collateral amounts in USD.
        debt_usd_amounts (pd.DataFrame): Dataframe of debt amounts in USD.
    """

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


def get_parquets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reads and returns parquet files for general, supply, collateral, and debt stats.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
        Dataframes containing general stats, supply stats, collateral stats, and debt stats.
    """

    general_stats = pd.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/general_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    supply_stats = pd.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/supply_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    collateral_stats = pd.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/collateral_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    debt_stats = pd.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/debt_stats.parquet",
        engine="fastparquet",
    ).set_index("Protocol")

    general_stats["TVL (USD)"] = (
        supply_stats["Total supply (USD)"] - general_stats["Total debt (USD)"]
    )
    return general_stats, supply_stats, collateral_stats, debt_stats


def get_multi_pie_chart(
    columns: list,
    tokens: list[str],
    collateral_stats: pd.DataFrame,
    debt_stats: pd.DataFrame,
    supply_stats: pd.DataFrame
) -> None:
    """
    Displays multiple pie charts for collateral, debt, and supply stats for different tokens.

    Args:
        columns (list): List of columns for displaying charts.
        tokens (list[str]): List of tokens to display stats for.
        collateral_stats (pd.DataFrame): Dataframe for collateral statistics.
        debt_stats (pd.DataFrame): Dataframe for debt statistics.
        supply_stats (pd.DataFrame): Dataframe for supply statistics.
    """

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
