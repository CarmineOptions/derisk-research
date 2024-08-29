import datetime
import logging
import math
from typing import Dict
import requests
import time

import pandas
import plotly.express
import streamlit

import src.helpers
import src.main_chart
import src.persistent_state
import src.settings
import src.swap_amm



def _remove_leading_zeros(address: str) -> str:
    while address[2] == '0':
        address = f'0x{address[3:]}'
    return address


def _get_available_liquidity(data: pandas.DataFrame, price: float, price_diff: float, bids: bool) -> float:
    price_lower_bound = max(0.95 * price, price - price_diff) if bids else price
    price_upper_bound = price if bids else min(1.05 * price, price + price_diff)
    return data.loc[data["price"].between(price_lower_bound, price_upper_bound), "quantity"].sum()


def add_ekubo_liquidity(
    data: pandas.DataFrame,
    collateral_token: str,
    debt_token: str,
) -> float:
    URL = "http://178.32.172.153/orderbook/"
    DEX = 'Ekubo'
    params = {
        "base_token": _remove_leading_zeros(collateral_token),
        "quote_token": _remove_leading_zeros(debt_token),
        "dex": DEX,
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        liquidity = response.json()
        try:
            bid_prices, bid_quantities = zip(*liquidity["bids"])
        except ValueError:
            time.sleep(300)
            add_ekubo_liquidity(data=data, collateral_token=collateral_token, debt_token=debt_token)
        else:
            bids = pandas.DataFrame(
                {
                    'price': bid_prices,
                    'quantity': bid_quantities,
                },
            )
            bids = bids.astype(float)
            bids.sort_values('price', inplace = True)
            price_diff = data['collateral_token_price'].diff().max()
            data['Ekubo_debt_token_supply'] = data['collateral_token_price'].apply(
                lambda x: _get_available_liquidity(
                    data=bids,
                    price=x,
                    price_diff=price_diff,
                    bids=True,
                )
            )
            data['debt_token_supply'] += data['Ekubo_debt_token_supply']
            return data

    logging.warning('Using collateral token as base token and debt token as quote token.')
    params = {
        "base_token": _remove_leading_zeros(debt_token),
        "quote_token": _remove_leading_zeros(collateral_token),
        "dex": DEX,
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        liquidity = response.json()
        try:
            ask_prices, ask_quantities = zip(*liquidity["asks"])
        except ValueError:
            time.sleep(5)
            add_ekubo_liquidity(data=data, collateral_token=collateral_token, debt_token=debt_token)
        else:
            asks = pandas.DataFrame(
                {
                    'price': ask_prices,
                    'quantity': ask_quantities,
                },
            )
            asks = asks.astype(float)
            asks.sort_values('price', inplace = True)
            data['Ekubo_debt_token_supply'] = data['collateral_token_price'].apply(
                lambda x: _get_available_liquidity(
                    data=asks,
                    price=x,
                    bids=False,
                )
            )
            data['debt_token_supply'] += data['Ekubo_debt_token_supply']
            return data

    return data

def create_stablecoin_bundle(data: Dict[str, pandas.DataFrame]) -> Dict[str, pandas.DataFrame]:
    """
    Creates a stablecoin bundle by merging relevant DataFrames for collateral tokens and debt tokens.
    
    For each collateral token specified in `src.settings.COLLATERAL_TOKENS`, this function finds the
    relevant stablecoin pairs from the provided `data` dictionary and merges the corresponding DataFrames
    based on the 'collateral_token_price' column. It combines the debt and liquidity data for multiple 
    stablecoin pairs and adds the result back to the `data` dictionary under a new key.

    Parameters:
    data (Dict[str, pandas.DataFrame]): A dictionary where the keys are token pairs and the values are 
                                        corresponding DataFrames containing price and supply data.

    Returns:
    Dict[str, pandas.DataFrame]: The updated dictionary with the newly created stablecoin bundle added.
    """
    
    # Iterate over all collateral tokens defined in the settings
    for collateral in src.settings.COLLATERAL_TOKENS:
        # Find all relevant pairs that involve the current collateral and one of the debt tokens
        relevant_pairs = [
            pair for pair in data.keys() 
            if collateral in pair and any(stablecoin in pair for stablecoin in src.settings.DEBT_TOKENS[:-1])
        ]
        combined_df = None  # Initialize a variable to store the combined DataFrame

        # Loop through each relevant pair
        for pair in relevant_pairs:
            df = data[pair]  # Get the DataFrame for the current pair

            if df.empty:
                # Log a warning if the DataFrame is empty and skip to the next pair
                logging.warning(f"Empty DataFrame for pair: {pair}")
                continue
                
            if combined_df is None:
                # If this is the first DataFrame being processed, use it as the base for combining
                combined_df = df.copy()
            else:
                # Merge the current DataFrame with the combined one on 'collateral_token_price'
                combined_df = pandas.merge(combined_df, df, on='collateral_token_price', suffixes=('', '_y'))

                # Sum the columns for debt and liquidity, adding the corresponding '_y' values
                for col in ['liquidable_debt', 'liquidable_debt_at_interval', 
                            '10kSwap_debt_token_supply', 'MySwap_debt_token_supply', 
                            'SithSwap_debt_token_supply', 'JediSwap_debt_token_supply', 
                            'debt_token_supply']:
                    combined_df[col] += combined_df[f'{col}_y']

                # Drop the '_y' columns after summing the relevant values
                combined_df.drop([col for col in combined_df.columns if col.endswith('_y')], axis=1, inplace=True)

        # Create a new pair name for the stablecoin bundle
        new_pair = f'{collateral}-{src.settings.STABLECOIN_BUNDLE_NAME}'
        # Add the combined DataFrame for this collateral to the data dictionary
        data[new_pair] = combined_df

    # Return the updated data dictionary
    return data


def main():
    streamlit.title("DeRisk")

    (
        zklend_main_chart_data,
        zklend_loans_data,
    ) = src.helpers.load_data(protocol='zkLend')
    # (
    #     hashstack_v0_main_chart_data,
    #     hashstack_v0_loans_data,
    # ) = src.helpers.load_data(protocol='Hashstack V0')
    # (
    #     hashstack_v1_main_chart_data,
    #     hashstack_v1_loans_data,
    # ) = src.helpers.load_data(protocol='Hashstack V1')
    (
        nostra_alpha_main_chart_data,
        nostra_alpha_loans_data,
    ) = src.helpers.load_data(protocol='Nostra Alpha')
    (
        nostra_mainnet_main_chart_data,
        nostra_mainnet_loans_data,
    ) = src.helpers.load_data(protocol='Nostra Mainnet')

    col1, _ = streamlit.columns([1, 3])
    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            # TODO
            options=["zkLend", "Nostra Alpha", "Nostra Mainnet"],
            default=["zkLend", "Nostra Alpha", "Nostra Mainnet"],
            # options=["zkLend", "Hashstack V0", "Hashstack V1", "Nostra Alpha", "Nostra Mainnet"],
            # default=["zkLend", "Hashstack V0", "Hashstack V1", "Nostra Alpha", "Nostra Mainnet"],
        )
        collateral_token = streamlit.selectbox(
            label="Select collateral token:",
            options=src.settings.COLLATERAL_TOKENS,
            index=0,
        )
        
        debt_token = streamlit.selectbox(
            label="Select debt token:",
            options=src.settings.DEBT_TOKENS,
            index=0,
        )
    stable_coin_pair = f"{collateral_token}-{src.settings.STABLECOIN_BUNDLE_NAME}"

    if(debt_token == collateral_token):
        streamlit.subheader(
            f":warning: You are selecting the same token for both collateral and debt.")   
        
    current_pair = f"{collateral_token}-{debt_token}"

    main_chart_data = pandas.DataFrame()
    # histogram_data = pandas.DataFrame()
    loans_data = pandas.DataFrame()

    protocol_main_chart_data_mapping = {
        'zkLend': create_stablecoin_bundle(zklend_main_chart_data)[current_pair],
        # 'Hashstack V0': hashstack_v0_main_chart_data[current_pair],
        # 'Hashstack V1': hashstack_v1_main_chart_data[current_pair],
        'Nostra Alpha': create_stablecoin_bundle(nostra_alpha_main_chart_data)[current_pair],
        'Nostra Mainnet': create_stablecoin_bundle(nostra_mainnet_main_chart_data)[current_pair],
    } if current_pair == stable_coin_pair else {
        'zkLend': zklend_main_chart_data[current_pair],
        # 'Hashstack V0': hashstack_v0_main_chart_data[current_pair],
        # 'Hashstack V1': hashstack_v1_main_chart_data[current_pair],
        'Nostra Alpha': nostra_alpha_main_chart_data[current_pair],
        'Nostra Mainnet': nostra_mainnet_main_chart_data[current_pair],
    }
    protocol_loans_data_mapping = {
        'zkLend': zklend_loans_data,
        # 'Hashstack V0': hashstack_v0_loans_data,
        # 'Hashstack V1': hashstack_v1_loans_data,
        'Nostra Alpha': nostra_alpha_loans_data,
        'Nostra Mainnet': nostra_mainnet_loans_data,
    }
    for protocol in protocols:
        protocol_main_chart_data = protocol_main_chart_data_mapping[protocol]
        if protocol_main_chart_data is None:
            streamlit.subheader(
                f":warning: No data for STRK and {src.settings.STABLECOIN_BUNDLE_NAME} bundle")   
            break
        if protocol_main_chart_data.empty:
            continue
        protocol_loans_data = protocol_loans_data_mapping[protocol]
        if main_chart_data.empty:
            main_chart_data = protocol_main_chart_data
        else:
            main_chart_data["liquidable_debt"] += protocol_main_chart_data["liquidable_debt"]
            main_chart_data["liquidable_debt_at_interval"] += protocol_main_chart_data["liquidable_debt_at_interval"]
        if loans_data.empty:
            loans_data = protocol_loans_data
        else:
            loans_data = pandas.concat([loans_data, protocol_loans_data])

    # Plot the liquidable debt against the available supply.
    collateral_token, debt_token = current_pair.split("-")

    if current_pair == stable_coin_pair:
        for stable_coin in src.settings.DEBT_TOKENS[:-1]:
            debt_token = stable_coin
            
            # Fetch underlying addresses and decimals
            collateral_token_underlying_address = src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[collateral_token]
            collateral_token_decimals = int(math.log10(src.settings.TOKEN_SETTINGS[collateral_token].decimal_factor))
            underlying_addresses_to_decimals = {collateral_token_underlying_address: collateral_token_decimals}

            # Fetch prices
            prices = src.helpers.get_prices(token_decimals=underlying_addresses_to_decimals)
            collateral_token_price = prices[collateral_token_underlying_address]

            # TODO: Add Ekubo start
            main_chart_data = main_chart_data.astype(float)
            debt_token_underlying_address = src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[debt_token]
            main_chart_data = add_ekubo_liquidity(
                data=main_chart_data,
                collateral_token=collateral_token_underlying_address,
                debt_token=debt_token_underlying_address,
            )
    else:
        # Fetch underlying addresses and decimals
        collateral_token_underlying_address = src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[collateral_token]
        collateral_token_decimals = int(math.log10(src.settings.TOKEN_SETTINGS[collateral_token].decimal_factor))
        underlying_addresses_to_decimals = {collateral_token_underlying_address: collateral_token_decimals}

        # Fetch prices
        prices = src.helpers.get_prices(token_decimals=underlying_addresses_to_decimals)
        collateral_token_price = prices[collateral_token_underlying_address]

        # TODO: Add Ekubo start
        main_chart_data = main_chart_data.astype(float)
        debt_token_underlying_address = src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[debt_token]
        main_chart_data = add_ekubo_liquidity(
            data=main_chart_data,
            collateral_token=collateral_token_underlying_address,
            debt_token=debt_token_underlying_address,
        )

    # TODO: Add Ekubo end
    figure = src.main_chart.get_main_chart_figure(
        data=main_chart_data,
        collateral_token=collateral_token,
        debt_token=src.settings.STABLECOIN_BUNDLE_NAME if current_pair == stable_coin_pair else debt_token,
        collateral_token_price=collateral_token_price,
    )
    streamlit.plotly_chart(figure_or_data=figure, use_container_width=True)

    main_chart_data['debt_to_supply_ratio'] = (
        main_chart_data['liquidable_debt_at_interval'] / main_chart_data['debt_token_supply']
    )
    example_rows = main_chart_data[
        (main_chart_data['debt_to_supply_ratio'] > 0.75)
        & (main_chart_data['collateral_token_price'] <= collateral_token_price)
    ]

    if not example_rows.empty:
        example_row = example_rows.sort_values('collateral_token_price').iloc[-1]

        def _get_risk_level(debt_to_supply_ratio: float) -> str:
            if debt_to_supply_ratio < 0.2:
                return 'low'
            elif debt_to_supply_ratio < 0.4:
                return 'medium'
            elif debt_to_supply_ratio < 0.6:
                'high'
            return 'very high'

        streamlit.subheader(
            f":warning: At price of {round(example_row['collateral_token_price'], 2)}, the risk of acquiring bad debt for "
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
    streamlit.dataframe(
        pandas.read_parquet(
            f"gs://{src.helpers.GS_BUCKET_NAME}/data/general_stats.parquet",
            engine='fastparquet',
        ),
    )
    streamlit.dataframe(
        pandas.read_parquet(
            f"gs://{src.helpers.GS_BUCKET_NAME}/data/utilization_stats.parquet",
            engine='fastparquet',
        ),
    )
    supply_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/supply_stats.parquet",
        engine='fastparquet',
    )
    collateral_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/collateral_stats.parquet",
        engine='fastparquet',
    )
    debt_stats = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/data/debt_stats.parquet",
        engine='fastparquet',
    )

    columns = streamlit.columns(4)
    tokens = list(src.settings.TOKEN_SETTINGS.keys())
    for column, token_1, token_2 in zip(columns, tokens[:4], tokens[4:]):
        with column:
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    collateral_stats,
                    values=f'{token} collateral',
                    names='Protocol',
                    title=f'{token} collateral',
                    color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
                )
                streamlit.plotly_chart(figure, True)
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    debt_stats,
                    values=f'{token} debt',
                    names='Protocol',
                    title=f'{token} debt',
                    color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
                )
                streamlit.plotly_chart(figure, True)
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    supply_stats,
                    values=f'{token} supply',
                    names='Protocol',
                    title=f'{token} supply',
                    color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
                )
                streamlit.plotly_chart(figure, True)

    last_update = src.persistent_state.load_pickle(path=src.persistent_state.LAST_UPDATE_FILENAME)
    last_timestamp = last_update["timestamp"]
    last_block_number = last_update["block_number"]
    date_str = datetime.datetime.utcfromtimestamp(int(last_timestamp))
    streamlit.write(f"Last updated {date_str} UTC, last block: {last_block_number}.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    streamlit.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
