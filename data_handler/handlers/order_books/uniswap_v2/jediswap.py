import asyncio
import math
from decimal import Decimal
from src.blockchain_call import func_call


def price_to_tick(price: Decimal, token_a_decimals: int, token_b_decimals: int) -> int:
    return round(Decimal(math.log(price / (10 ** (token_a_decimals - token_b_decimals))) / math.log(1.0001)))


async def main():
    pool_address = "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a"  # ETH/USDC

    token_a_decimals = 18  # ETH
    token_b_decimals = 6  # USDC

    response = await func_call(pool_address, "get_reserves", [])

    reserve_0 = Decimal(response[0]) / 10**token_a_decimals
    reserve_1 = Decimal(response[2]) / 10**token_b_decimals

    curr_price = reserve_1 / reserve_0
    min_price = curr_price * Decimal("0.1")
    max_price = curr_price * Decimal("1.9")

    min_tick = price_to_tick(min_price, token_a_decimals, token_b_decimals)
    curr_tick = price_to_tick(curr_price, token_a_decimals, token_b_decimals)
    max_tick = price_to_tick(max_price, token_a_decimals, token_b_decimals)

    bids_1, asks_1 = [], []
    constant_product = reserve_0 * reserve_1
    current_a_amount = reserve_0
    current_b_amount = reserve_1

    # Reserves calculation method
    # tvl_a and tvl_b remain constant for all tick spacings
    for tick in range(curr_tick - 1, min_tick, -10):
        price = (Decimal("1.0001") ** tick) * 10 ** (token_a_decimals - token_b_decimals)
        new_eth_reserve = Decimal((constant_product / price)).sqrt()
        new_usdc_reserve = price * new_eth_reserve
        quantity = current_b_amount - new_usdc_reserve
        bids_1.append((price, quantity))
    tvl_b_1 = (sum([x[1] for x in bids_1])) * Decimal(1.0035) / (10 ** (token_a_decimals - token_b_decimals))

    for tick in range(curr_tick + 1, max_tick, 10):
        price = (Decimal("1.0001") ** tick) * 10 ** (token_a_decimals - token_b_decimals)
        new_eth_reserve = Decimal((constant_product / price)).sqrt()
        quantity = current_a_amount - new_eth_reserve
        asks_1.append((price, quantity))
    tvl_a_1 = (sum([x[1] for x in asks_1])) * Decimal(3800) / Decimal(10 ** (token_a_decimals - token_b_decimals))

    # Using supply function logic
    bids_2, asks_2 = [], []
    for tick in range(curr_tick - 1, min_tick, -10):
        price = (Decimal("1.0001") ** tick) * 10 ** (token_a_decimals - token_b_decimals)
        quantity = (price * constant_product).sqrt() * (
            Decimal("1") -
            Decimal("0.95").sqrt()
        )
        bids_2.append((price, quantity))
    tvl_b_2 = (sum([x[1] for x in bids_2])) * Decimal(1.0035) / (10 ** (token_a_decimals - token_b_decimals))

    for tick in range(curr_tick + 1, max_tick, 10):
        price = (Decimal("1.0001") ** tick) * 10 ** (token_a_decimals - token_b_decimals)
        quantity = (price * constant_product).sqrt() * (
            Decimal("1") -
            Decimal("0.95").sqrt()
        )
        asks_2.append((price, quantity))
    tvl_a_2 = (sum([x[1] for x in asks_2])) * Decimal(3800) / Decimal(10 ** (token_a_decimals - token_b_decimals))
    print()

if __name__ == '__main__':
    # To run put into De Risk project
    asyncio.run(main())
