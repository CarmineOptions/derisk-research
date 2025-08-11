import asyncio
import json
import logging

from celery import shared_task
from shared.redis_client import redis_client
from shared.amms import SwapAmm

logger = logging.getLogger(__name__)

@shared_task(name="fetch_balance_for_pools")
def fetch_balance_for_pools():
    """
    Load loan data and main chart data for the specified protocol.
    :param protocol_name: Protocol name.
    :param state: State to load data for.
    :return: DataFrames containing loan data and main chart data.
    """
    logger.info(f"Run fetch_balance_for_pools")
    swap_amm = SwapAmm()
    swap_amm.__init__()
    result = asyncio.run(swap_amm.get_balance())
    data = {}
    for symbol, pool in result.items():
        for token in pool:
            data[f"{symbol}:{token.address}"] = token.balance_base
    redis_client.set("pool_balances", json.dumps(data))


if __name__ == "__main__":
    fetch_balance_for_pools()
