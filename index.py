import asyncio
import decimal
import pandas
from compute import (
    decimal_range,
    get_amm_supply_at_price,
    simulate_liquidations_under_absolute_price_change,
)
import db
import constants
from classes import Prices, State
from data import get_events
from swap_liquidity import SwapAmm


def get_range(start, stop, step):
    return [
        x
        for x in decimal_range(
            # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
            start=decimal.Decimal(start),
            stop=decimal.Decimal(stop),
            # TODO: make it dependent on the collateral token
            step=decimal.Decimal(step),
        )
    ]


# TODO: move this somewhere
def get_pair_range(c, b):
    if c == "ETH" and b == "wBTC":
        return get_range("0.02", "0.2", "0.0015")
    if c == "wBTC" and b == "ETH":
        return get_range("5", "25", "0.375")
    if c == "ETH":
        return get_range("1000", "3000", "50")
    if c == "wBTC":
        return get_range("20000", "35000", "250")
    raise ValueError(f"Wrong pair {c}-{b}")


def load_graph_data(state, prices, collateral_token, borrowings_token):
    data = pandas.DataFrame(
        {"collateral_token_price": get_pair_range(collateral_token, borrowings_token)},
    )
    # TOOD: needed?
    # data['collateral_token_price_multiplier'] = data['collateral_token_price_multiplier'].map(decimal.Decimal)
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
        lambda x: simulate_liquidations_under_absolute_price_change(
            prices=prices,
            collateral_token=collateral_token,
            collateral_token_price=x,
            state=state,
            borrowings_token=borrowings_token,
        )
    )

    # TODO
    data["max_borrowings_to_be_liquidated_at_interval"] = (
        data["max_borrowings_to_be_liquidated"].diff().abs()
    )
    # TODO: drops also other NaN, if there are any
    data.dropna(inplace=True)

    # Setup the AMM.
    jediswap = SwapAmm("JediSwap")
    jediswap.add_pool(
        "ETH",
        "USDC",
        "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    )
    jediswap.add_pool(
        "DAI",
        "ETH",
        "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    )
    jediswap.add_pool(
        "ETH",
        "USDT",
        "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    )
    jediswap.add_pool(
        "wBTC",
        "ETH",
        "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    )
    jediswap.add_pool(
        "wBTC",
        "USDC",
        "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    )
    jediswap.add_pool(
        "wBTC",
        "USDT",
        "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    )
    jediswap.add_pool(
        "DAI",
        "wBTC",
        "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",
    )
    jediswap.add_pool(
        "DAI",
        "USDC",
        "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    )
    jediswap.add_pool(
        "DAI",
        "USDT",
        "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    )
    jediswap.add_pool(
        "USDC",
        "USDT",
        "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    )
    asyncio.run(jediswap.get_balance())

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: get_amm_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            borrowings_token=borrowings_token,
            amm=jediswap,
        )
    )
    return data


def get_events() -> pandas.DataFrame:
    connection = db.establish_connection()
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{constants.Protocol.ZKLEND.value}'
      AND
          key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
      ORDER BY
          block_number, id ASC;
      """,
        con=connection,
    )
    connection.close()
    zklend_events.set_index("id", inplace=True)
    return zklend_events


state = State()

for _, event in get_events().iterrows():
    state.process_event(event)

prices = Prices()


pairs = [
    ("wBTC", "ETH"),
    ("ETH", "wBTC"),
    ("ETH", "USDC"),
    ("ETH", "USDT"),
    ("ETH", "DAI"),
    ("wBTC", "USDC"),
    ("wBTC", "USDT"),
    ("wBTC", "DAI"),
]

for pair in pairs:
    print(pair[0], pair[1])
    c = pair[0]
    b = pair[1]
    data = load_graph_data(
        state=state, prices=prices, collateral_token=c, borrowings_token=b
    )
    filename = f"{c}-{b}.csv"
    data.to_csv(filename, index=False)
