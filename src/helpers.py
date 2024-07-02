from typing import Iterator
import logging
import os
import time

import google.cloud.storage
import pandas
import requests
import starknet_py.cairo.felt

import src.blockchain_call
import src.db
import src.settings
import src.types



# TODO: rename
GS_BUCKET_NAME = "derisk-persistent-state/test2"



def get_events(
    addresses: tuple[str, ...],
    event_names: tuple[str, ...],
    start_block_number: int = 0,
) -> pandas.DataFrame:
    connection = src.db.establish_connection()
    events = pandas.read_sql(
        sql=f"""
            SELECT
                *
            FROM
                starkscan_events
            WHERE
                from_address IN {addresses}
            AND
                key_name IN {event_names}
            AND
                block_number >= {start_block_number}
            ORDER BY
                block_number, id ASC;
        """,
        con=connection,
    )
    connection.close()
    return events.set_index("id")


def float_range(start: float, stop: float, step: float) -> Iterator[float]:
    while start < stop:
        yield start
        start += step


def get_collateral_token_range(
    collateral_token_underlying_address: str,
    collateral_token_price: float,
) -> list[float]:
    # TODO: improve
    STEPS = {
        "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": 100.0,  # ETH
        "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac": 2_000.0,  # WBTC
        "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d": 0.025,  # STRK
    }
    return list(
        float_range(
            start = STEPS[collateral_token_underlying_address],
            stop = collateral_token_price * 1.2,
            step = STEPS[collateral_token_underlying_address],
        )
    )


# TODO: replace these mappings 
UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    "DAI V2": "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad",
}


def load_data(protocol: str) -> tuple[dict[str, pandas.DataFrame], pandas.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in src.settings.PAIRS:
        collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split('-')
        collateral_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[collateral_token_underlying_symbol]
        debt_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[debt_token_underlying_symbol]
        underlying_addresses_pair = f"{collateral_token_underlying_address}-{debt_token_underlying_address}"
        try:
            main_chart_data[pair] = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/{underlying_addresses_pair}.parquet")
        except FileNotFoundError:
            main_chart_data[pair] = pandas.DataFrame()
    loans_data = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/loans.parquet")
    return main_chart_data, loans_data


async def get_symbol(token_address: str) -> str:
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1. 
    if token_address == '0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad':
        return 'DAI V2'
    symbol = await src.blockchain_call.func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return starknet_py.cairo.felt.decode_shortstring(symbol[1])
    return starknet_py.cairo.felt.decode_shortstring(symbol[0])


def get_price(token: str, decimals: int) -> float:
    USDC = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8'
    if token == USDC:
        return 1.0

    # TODO: load NSTSTRK price from somewhere else.
    NSTSTRK = '0x04619e9ce4109590219c5263787050726be63382148538f3f936c22aa87d2fc2'
    if token == NSTSTRK:
        return 0.7

    # TODO: load UNO price from somewhere else.
    UNO = '0x0719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34'
    if token == UNO:
        return 0.99

    URL = "https://starknet.api.avnu.fi/internal/swap/quotes-with-prices"
    SELL_AMOUNT_USDC = 10
    DECIMALS_USDC = 6

    params = {
        "sellTokenAddress": USDC,
        "buyTokenAddress": token,
        "sellAmount": hex(SELL_AMOUNT_USDC * (10 ** DECIMALS_USDC)),
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        token_parameters = response.json()['prices']
        if not token_parameters:
            # TODO: add retry count?
            logging.warning('Failed to get prices for token = {}, sleeping and retrying.'.format(token))
            time.sleep(0.1)
            return get_price(token = token, decimals = decimals)

        def _compute_token_price(buy_amount: int) -> float:
            buy_amount_per_usdc = buy_amount / SELL_AMOUNT_USDC / (10 ** decimals)
            return 1 / buy_amount_per_usdc

        max_buy_amount = max(int(x['buyAmount'], base = 16) for x in token_parameters)
        return _compute_token_price(max_buy_amount)
    else:
        response.raise_for_status()


def get_prices(token_decimals: dict[str, int]) -> dict[str, float]:
    prices = {}
    for token, decimals in token_decimals.items():
        prices[token] = get_price(token = token, decimals = decimals)
    return prices


def upload_file_to_bucket(source_path: str, target_path: str):
    bucket_name, folder = GS_BUCKET_NAME.split('/')
    target_path = f'{folder}/{target_path}'

    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = google.cloud.storage.Client.from_service_account_json(os.getenv("CREDENTIALS_PATH"))

    # Get the target bucket.
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logging.info(f"File = {source_path} uploaded to = gs://{GS_BUCKET_NAME}/{target_path}.")


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
    directory = path.rstrip(path.split('/')[-1])
    if not directory == '':
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine = 'fastparquet', compression='gzip')
    src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def add_leading_zeros(hash: str) -> str:
    '''
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to  
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    '''
    return '0x' + hash[2:].zfill(64)


def get_addresses(
    token_parameters: src.types.TokenParameters, 
    underlying_address: str | None = None,
    underlying_symbol: str | None = None,
) -> list[str]:
    # Up to 2 addresses can match the given `underlying_address` or `underlying_symbol`.
    if underlying_address:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_address == underlying_address
        ]
    elif underlying_symbol:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_symbol == underlying_symbol
        ]
    else:
        raise ValueError(
            'Both `underlying_address` =  {} or `underlying_symbol` = {} are not specified.'.format(
                underlying_address, 
                underlying_symbol,
            )
        )
    assert len(addresses) <= 2
    return addresses


def get_underlying_address(
    token_parameters: src.types.TokenParameters, 
    underlying_symbol: str,
) -> str:
    # One underlying address at maximum can match the given `underlying_symbol`.
    underlying_addresses = {
        x.underlying_address
        for x in token_parameters.values()
        if x.underlying_symbol == underlying_symbol
    }
    if not underlying_addresses:
        return ''
    assert len(underlying_addresses) == 1
    return list(underlying_addresses)[0]