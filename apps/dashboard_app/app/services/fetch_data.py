import time
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from decimal import Decimal
from dotenv import load_dotenv
from shared.constants import TOKEN_SETTINGS
import os

load_dotenv()
NODE_URL = os.getenv("NODE_URL")

client = FullNodeClient(node_url=NODE_URL)


async def fetch_events(address, from_block, to_block="latest", chunk_size=150):
    """Fetch events from the blockchain with pagination support."""
    continuation_token = None
    all_events = []

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

        all_events.extend(response.events)
        continuation_token = response.continuation_token

        if not continuation_token:
            print("No more events to fetch.")
            break

    return all_events


async def get_token_name_from_tx(tx):
    """Extract token name from transaction data."""
    for token_symbol, token_setting in TOKEN_SETTINGS.items():
        if int(token_setting.address, 16) == tx.calldata[1]:
            return token_symbol, token_setting
    return None, None


# FIXME: Close Trade transactions have different calldata structure
async def get_token_name_from_close_tx(tx):
    """Extract token name from close transaction data."""
    for token_symbol, token_setting in TOKEN_SETTINGS.items():
        if int(token_setting.address, 16) in tx.calldata:
            return token_symbol, token_setting
    return None, None


async def process_trade_open(event):
    """Process a trade open event and return formatted data."""
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
            "%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)
        )

        user_address = tx.sender_address
        return {
            user_address: {
                "token": token_name,
                "price": "price --",
                "amount": amount,
                "timestamp": block_timestamp,
                "is_sold": True,
            }
        }
    except Exception as e:
        print(f"Error processing TradeOpen: {e}")
        return None


async def process_trade_close(event):
    """Process a trade close event and return formatted data."""
    try:
        tx = await client.get_transaction(event.transaction_hash)
        token_name, token_setting = await get_token_name_from_close_tx(tx)

        if not token_name:
            return None

        amount_low = event.data[2]
        amount_high = event.data[3]
        amount = (amount_high << 128) + amount_low
        amount = Decimal(amount) / token_setting.decimal_factor

        block = await client.get_block(block_number=event.block_number)
        block_timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(block.timestamp)
        )

        user_address = tx.sender_address
        return {
            user_address: {
                "token": token_name,
                "price": "price --",
                "amount": amount,
                "timestamp": block_timestamp,
                "is_sold": False,
            }
        }
    except Exception as e:
        print(f"Error processing TradeClose: {e}")
        return None


async def get_events_by_hash():
    """Main function to get and process trade events."""
    contract_address = (
        "0x47472e6755afc57ada9550b6a3ac93129cc4b5f98f51c73e0644d129fd208d9"
    )
    from_block = 1284758

    events = await fetch_events(contract_address, from_block)
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
