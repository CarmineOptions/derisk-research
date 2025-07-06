import time
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from decimal import Decimal
from dotenv import load_dotenv
from shared.constants import TOKEN_SETTINGS
import os
import logging
import asyncio
from dashboard_app.app.schemas.user_transaction import UserTransaction

load_dotenv()
NODE_URL = os.getenv("NODE_URL")

client = FullNodeClient(node_url=NODE_URL)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


async def fetch_events_chunk(address, from_block, to_block, chunk_size=150) -> list:
    """
    Fetch events for a specific block range with pagination support.

    :param address: str
        The address of the contract to fetch events from.
    :param from_block: int
        The block number to start fetching events from.
    :param to_block: int
        The block number to stop fetching events at.
    :param chunk_size: int
        The number of events to fetch in each request. Default is 150.
    :returns: list
        A list of events fetched from the blockchain.
    """
    continuation_token = None
    chunk_events = []

    while True:
        response = await client.get_events(
            address=address,
            from_block_number=from_block,
            to_block_number=to_block,
            keys=[
                [
                    hex(get_selector_from_name("TradeOpen")),
                    hex(get_selector_from_name("TradeClose")),
                ]
            ],
            chunk_size=chunk_size,
            continuation_token=continuation_token,
        )

        chunk_events.extend(response.events)
        continuation_token = response.continuation_token

        if not continuation_token:
            logging.info(
                f"Fetched {len(chunk_events)} events for blocks {from_block} to {to_block}."
            )
            break

    return chunk_events


async def fetch_events(
    address, from_block, to_block, chunk_size=150, concurrent_requests=5
) -> list:
    """
    Fetch events from the blockchain with concurrent requests for better performance.

    :param address: str
        The address of the contract to fetch events from.
    :param from_block: int
        The block number to start fetching events from.
    :param to_block: int
        The block number to stop fetching events at. Default is "latest".
    :param chunk_size: int
        The number of events to fetch in each request. Default is 150.
    :param concurrent_requests: int
        The number of concurrent requests to make. Default is 5.
    :returns: list
        A list of events fetched from the blockchain.
    """

    total_blocks = to_block - from_block + 1
    blocks_per_chunk = max(1, total_blocks // concurrent_requests)

    chunks = []
    for i in range(0, concurrent_requests):
        chunk_from = from_block + (i * blocks_per_chunk)
        chunk_to = min(to_block, chunk_from + blocks_per_chunk - 1)
        if chunk_from <= chunk_to:
            chunks.append((chunk_from, chunk_to))

    tasks = []
    for chunk_from, chunk_to in chunks:
        tasks.append(fetch_events_chunk(address, chunk_from, chunk_to, chunk_size))

    chunk_results = await asyncio.gather(*tasks)
    all_events = []
    for events in chunk_results:
        all_events.extend(events)

    logging.info(
        f"Fetched {len(all_events)} events in total using {len(tasks)} concurrent requests."
    )
    return all_events


# FIXME: Close Trade transactions have different calldata structure
async def get_token_name_from_tx(tx: dict) -> tuple:
    """
    Extract token name from transaction data.

    :param tx: dict
        The transaction data containing information about the token.
    :returns: tuple
        A tuple containing the token name and its settings.
    """
    for token_symbol, token_setting in TOKEN_SETTINGS.items():
        if int(token_setting.address, 16) == tx.calldata[1]:
            return token_symbol, token_setting
    return None, None


async def process_trade_open(event: dict) -> UserTransaction:
    """
    Process a trade open event and return formatted data.
    event: dict
        The event data containing information about the trade open.
    get_block: function
        Function to get block data from the blockchain.
    get_transaction: function
        Function to get transaction data from the blockchain.
    :returns: UserTransaction
        A UserTransaction object containing the processed trade data.
    """

    try:
        tx = await client.get_transaction(event.transaction_hash)
        token_name, token_setting = await get_token_name_from_tx(tx)

        if not token_name:
            return None

        amount_low = event.data[2]
        amount_high = event.data[3]
        amount = (amount_high << 128) + amount_low
        amount = Decimal(amount) / token_setting.decimal_factor

        block = await client.get_block(block_number=event.block_number)
        block_timestamp = time.strftime(
            TIMESTAMP_FORMAT, time.localtime(block.timestamp)
        )

        user_address = hex(tx.sender_address)
        return UserTransaction(
            user_address=user_address,
            token=token_name,
            price="price --",
            amount=amount,
            timestamp=block_timestamp,
            is_sold=True,
        )
    except KeyError as e:
        logging.error(f"KeyError processing TradeOpen: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing TradeOpen: {e}")
        return None


async def process_trade_close(event: dict) -> UserTransaction:
    """Process a trade close event and return formatted data.

    event: dict
        The event data containing information about the trade close.
    get_block: function
        Function to get block data from the blockchain.
    get_transaction: function
        Function to get transaction data from the blockchain.
    :returns: UserTransaction
        A UserTransaction object containing the processed trade data.
    """
    try:
        tx = await client.get_transaction(event.transaction_hash)
        token_name, token_setting = await get_token_name_from_tx(tx)

        if not token_name:
            return None

        amount_low = event.data[2]
        amount_high = event.data[3]
        amount = (amount_high << 128) + amount_low
        amount = Decimal(amount) / token_setting.decimal_factor

        block = await client.get_block(block_number=event.block_number)
        block_timestamp = time.strftime(
            TIMESTAMP_FORMAT, time.localtime(block.timestamp)
        )

        user_address = hex(tx.sender_address)
        return UserTransaction(
            user_address=user_address,
            token=token_name,
            price="price --",
            amount=amount,
            timestamp=block_timestamp,
            is_sold=False,
        )
    except KeyError as e:
        logging.error(f"KeyError processing TradeClose: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing TradeClose: {e}")
        return None


async def get_events_by_hash():
    """Main function to get and process trade events."""
    CONTRACT_ADDRESS = "0x47472e6755afc57ada9550b6a3ac93129cc4b5f98f51c73e0644d129fd208d9"  # adress of the contract that have all the events
    from_block = 1284758  # change this to the block number you want to start from

    to_block = await client.get_block_number()
    events = await fetch_events(CONTRACT_ADDRESS, from_block, to_block)
    trade_open = []
    trade_close = []

    for event in events:
        if event.keys[0] == (get_selector_from_name("TradeOpen")):
            result = await process_trade_open(event)
            if result:
                trade_open.append(result)

        elif event.keys[0] == (get_selector_from_name("TradeClose")):
            result = await process_trade_close(event)
            if result:
                trade_close.append(result)

    return trade_open, trade_close


def filter_wallet_id(events: list, wallet_id: str) -> list:
    """Filter the events given a wallet id
    wallet_id: string
        The wallet address to filter the events, given as an integer
    :returns: list
        A list containing the filtered events.
    """
    return [event for event in events if event.user_address == wallet_id]


async def get_history_by_wallet_id(wallet_id: str) -> tuple:
    """Filter the events given a wallet id

    wallet_id: string
        The wallet address to filter the events, MUST be in hexadecimal format
    :returns: tuple
        A tuple containing the filtered trade open and trade close events.
    """
    trade_open, trade_close = await get_events_by_hash()
    filtered_trade_open = filter_wallet_id(trade_open, wallet_id)
    filtered_trade_close = filter_wallet_id(trade_close, wallet_id)

    return filtered_trade_open, filtered_trade_close
