import asyncio
import decimal
import json
import time

import pandas

import src.constants
import src.db
import src.hashstack
import src.nostra
import src.persistent_state
import src.swap_liquidity
import src.zklend


def get_range(start, stop, step):
    return [
        x
        for x in src.zklend.decimal_range(
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
        return get_range("0", "0.2", "0.0015")
    if c == "wBTC" and b == "ETH":
        return get_range("0", "25", "0.375")
    if c == "ETH":
        return get_range("50", "2500", "50")
    if c == "wBTC":
        return get_range("250", "32000", "250")
    raise ValueError(f"Wrong pair {c}-{b}")


def generate_graph_data(state, prices, swap_amm, collateral_token, borrowings_token):
    data = pandas.DataFrame(
        {"collateral_token_price": get_pair_range(
            collateral_token, borrowings_token)},
    )
    # TOOD: needed?
    # data['collateral_token_price_multiplier'] = data['collateral_token_price_multiplier'].map(decimal.Decimal)
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
        lambda x: src.zklend.simulate_liquidations_under_absolute_price_change(
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

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: src.zklend.get_amm_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            borrowings_token=borrowings_token,
            amm=swap_amm,
        )
    )
    return data


def generate_and_store_graph_data(state, prices, swap_amm, pair):
    t0 = time.time()
    print("generating graph for", pair, flush=True)
    c = pair[0]
    b = pair[1]
    data = generate_graph_data(state, prices, swap_amm, c, b)
    filename = f"data/{c}-{b}.csv"
    data.to_csv(filename, index=False)
    print(filename, "done in", time.time() - t0, flush=True)


def get_events(block_number) -> pandas.DataFrame:
    connection = src.db.establish_connection()
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{src.constants.Protocol.ZKLEND.value}'
      AND
          key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
      AND
          block_number > {block_number}
      ORDER BY
          block_number, id ASC;
      """,
        con=connection,
    )
    connection.close()
    zklend_events.set_index("id", inplace=True)
    return zklend_events


def my_process(msg):
    print(f"Hello, this is process {msg}", flush=True)
    return msg


def update_data(state):
    t0 = time.time()
    print(f"Updating CSV data from {state.last_block_number}...", flush=True)
    zklend_events = get_events(state.last_block_number)
    hashstack_events = src.hashstack.get_hashstack_events()
    nostra_events = src.nostra.get_nostra_events()
    print(f"got events in {time.time() - t0}s", flush=True)

    new_latest_block = zklend_events["block_number"].max()
    state.update_block_number(new_latest_block)

    t1 = time.time()

    # Iterate over ordered events to obtain the final state of each user.
    for _, event in zklend_events.iterrows():
        state.process_event(event)

    hashstack_state = src.hashstack.State()
    for _, hashstack_event in hashstack_events.iterrows():
        hashstack_state.process_event(event=hashstack_event)

    nostra_state = src.nostra.State()
    for _, nostra_event in nostra_events.iterrows():
        nostra_state.process_event(event=nostra_event)

    print(f"updated state in {time.time() - t1}s", flush=True)

    t_prices = time.time()
    prices = src.swap_liquidity.Prices()

    print(f"prices in {time.time() - t_prices}s", flush=True)

    t_swap = time.time()

    swap_amms = asyncio.run(src.swap_liquidity.SwapAmm().init())

    print(f"swap in {time.time() - t_swap}s", flush=True)

    pairs = [
        # ("wBTC", "ETH"),
        # ("ETH", "wBTC"),
        ("ETH", "USDC"),
        ("ETH", "USDT"),
        ("ETH", "DAI"),
        ("wBTC", "USDC"),
        ("wBTC", "USDT"),
        ("wBTC", "DAI"),
    ]

    t2 = time.time()

    [generate_and_store_graph_data(
        state, prices, swap_amms, pair) for pair in pairs]
    [
        src.hashstack.generate_and_store_graph_data(
            hashstack_state, prices, swap_amms, pair)
        for pair in pairs
    ]
    [
        src.nostra.generate_and_store_graph_data(
            nostra_state, prices, swap_amms, pair)
        for pair in pairs
    ]

    print(f"updated graphs in {time.time() - t2}s", flush=True)

    histogram_data = [
        {
            "token": token,
            "borrowings": user_state.token_states[token].borrowings
            * prices.prices[token]
            / 10 ** src.constants.get_decimals(token),
        }
        for user_state in state.user_states.values()
        for token in src.constants.symbol_decimals_map.keys()
        if token[0] != "z"
    ]
    hashstack_histogram_data = [
        {
            "token": token,
            "borrowings": (
                loan.borrowings.amount
                if loan.borrowings.market == token
                else decimal.Decimal("0")
            )
            * prices.prices[token]
            / 10 ** src.constants.get_decimals(token),
        }
        for user_state in hashstack_state.user_states.values()
        for loan in user_state.loans.values()
        for token in src.constants.symbol_decimals_map.keys()
        if token[0] != "z"
    ]
    nostra_histogram_data = [
        {
            "token": token,
            "borrowings": user_state.token_states[token].debt
            * prices.prices[token]
            / 10 ** src.constants.get_decimals(token),
        }
        for user_state in nostra_state.user_states.values()
        for token in src.constants.symbol_decimals_map.keys()
        if token[0] != "z"
    ]

    pandas.DataFrame(histogram_data).to_csv("data/histogram.csv", index=False)
    pandas.DataFrame(hashstack_histogram_data).to_csv(
        "hashstack_data/histogram.csv", index=False
    )
    pandas.DataFrame(nostra_histogram_data).to_csv(
        "nostra_data/histogram.csv", index=False
    )

    for user, user_state in state.user_states.items():
        risk_adjusted_collateral_usd = src.zklend.compute_risk_adjusted_collateral_usd(
            user_state=user_state,
            prices=prices.prices,
        )
        borrowings_usd = src.zklend.compute_borrowings_usd(
            user_state=user_state,
            prices=prices.prices,
        )
        health_factor = src.zklend.compute_health_factor(
            risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
            borrowings_usd=borrowings_usd,
        )
        user_state.health_factor = health_factor

    class BadUser:
        def __init__(self, address, user_state):
            self.health_factor = user_state.health_factor
            self.address = address
            self.loan_size = decimal.Decimal("0")
            self.collateral_size = decimal.Decimal("0")
            self.collateral = {}
            self.borrowings = {}
            self.formatted_collateral = ""
            self.formatted_borrowings = ""
            self.calculate(user_state)
            self.format()

        def calculate(self, user_state):
            for token, token_state in user_state.token_states.items():
                if token_state.z_token:
                    continue
                if token_state.borrowings > decimal.Decimal("0"):
                    tokens = (
                        token_state.borrowings /
                        src.constants.TOKEN_DECIMAL_FACTORS[token]
                    )
                    self.borrowings[token] = (
                        self.borrowings.get(
                            token, decimal.Decimal("0")) + tokens
                    )
                    self.loan_size += tokens * prices.prices[token]
                if (
                    token_state.collateral_enabled
                    and token_state.deposit > decimal.Decimal("0")
                ):
                    tokens = (
                        token_state.deposit /
                        src.constants.TOKEN_DECIMAL_FACTORS[token]
                    )
                    self.collateral[token] = (
                        self.collateral.get(
                            token, decimal.Decimal("0")) + tokens
                    )
                    self.collateral_size += (
                        tokens
                        * prices.prices[token]
                        * src.constants.COLLATERAL_FACTORS[token]
                    )

        def format(self):
            for token, size in self.collateral.items():
                if self.formatted_collateral != "":
                    self.formatted_collateral += ", "
                formatted_size = format(size, ".4f")
                self.formatted_collateral += f"{token}: {formatted_size}"
            for token, size in self.borrowings.items():
                if self.formatted_borrowings != "":
                    self.formatted_borrowings += ", "
                formatted_size = format(size, ".4f")
                self.formatted_borrowings += f"{token}: {formatted_size}"

    small_bad_users = []
    big_bad_users = []

    for user, user_state in state.user_states.items():
        if user_state.health_factor < 1 and user_state.health_factor > 0.7:
            bad_user = BadUser(address=user, user_state=user_state)
            if bad_user.loan_size > 100:
                big_bad_users.append(bad_user)
            else:
                small_bad_users.append(bad_user)

    big_bad_users = sorted(
        big_bad_users, key=lambda x: x.health_factor, reverse=False)
    small_bad_users = sorted(
        small_bad_users, key=lambda x: x.health_factor, reverse=False
    )

    n = 20

    bbu_data = {
        "User": [user.address for user in big_bad_users[:n]],
        "Protocol": ["zkLend" for user in big_bad_users[:n]],
        "Health factor": [user.health_factor for user in big_bad_users[:n]],
        "Borrowing in USD": [user.loan_size for user in big_bad_users[:n]],
        "Risk adjusted collateral in USD": [
            user.collateral_size for user in big_bad_users[:n]
        ],
        "Collateral": [user.formatted_collateral for user in big_bad_users[:n]],
        "Borrowings": [user.formatted_borrowings for user in big_bad_users[:n]],
    }

    sbu_data = {
        "User": [user.address for user in small_bad_users[:n]],
        "Protocol": ["zkLend" for user in small_bad_users[:n]],
        "Health factor": [user.health_factor for user in small_bad_users[:n]],
        "Borrowing in USD": [user.loan_size for user in small_bad_users[:n]],
        "Risk adjusted collateral in USD": [
            user.collateral_size for user in small_bad_users[:n]
        ],
        "Collateral": [user.formatted_collateral for user in small_bad_users[:n]],
        "Borrowings": [user.formatted_borrowings for user in small_bad_users[:n]],
    }
    pandas.DataFrame(bbu_data).to_csv(
        "data/large_loans_sample.csv", index=False)
    pandas.DataFrame(sbu_data).to_csv(
        "data/small_loans_sample.csv", index=False)

    zklend_loan_stats = pandas.DataFrame()
    zklend_loan_stats["User"] = [
        user
        for user in state.user_states.keys()
    ]
    zklend_loan_stats["Protocol"] = "zkLend"
    zklend_loan_stats["Borrowing in USD"] = zklend_loan_stats.apply(
        lambda x: src.zklend.compute_borrowings_usd(
            user_state=state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    zklend_loan_stats[
        "Risk adjusted collateral in USD"
    ] = zklend_loan_stats.apply(
        lambda x: src.zklend.compute_risk_adjusted_collateral_usd(
            user_state=state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    zklend_loan_stats["Health factor"] = zklend_loan_stats.apply(
        lambda x: src.zklend.compute_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            borrowings_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )
    zklend_loan_stats["Standardized health factor"] = zklend_loan_stats.apply(
        lambda x: src.zklend.compute_standardized_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            borrowings_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )

    hashstack_loan_stats = pandas.DataFrame()
    hashstack_loan_stats["User"] = [
        user
        for user, user_state in hashstack_state.user_states.items()
        for _ in user_state.loans.keys()
    ]
    hashstack_loan_stats["Protocol"] = "Hashstack"
    hashstack_loan_stats["Loan ID"] = [
        loan_id
        for user_state in hashstack_state.user_states.values()
        for loan_id in user_state.loans.keys()
    ]
    hashstack_loan_stats["Borrowing in USD"] = hashstack_loan_stats.apply(
        lambda x: src.hashstack.compute_borrowings_amount_usd(
            borrowings=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .borrowings,
            prices=prices.prices,
        ),
        axis=1,
    )
    hashstack_loan_stats = hashstack_loan_stats[hashstack_loan_stats['Borrowing in USD'] > decimal.Decimal("0")]
    hashstack_loan_stats[
        "Risk adjusted collateral in USD"
    ] = hashstack_loan_stats.apply(
        lambda x: src.hashstack.compute_collateral_current_amount_usd(
            collateral=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .collateral,
            prices=prices.prices,
        ),
        axis=1,
    )
    hashstack_loan_stats["Health factor"] = hashstack_loan_stats.apply(
        lambda x: src.hashstack.compute_health_factor(
            borrowings=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .borrowings,
            collateral=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .collateral,
            prices=prices.prices,
            user=x["User"],
        ),
        axis=1,
    )
    hashstack_loan_stats["Standardized health factor"] = hashstack_loan_stats.apply(
        lambda x: src.hashstack.compute_standardized_health_factor(
            borrowings=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .borrowings,
            collateral=hashstack_state.user_states[x["User"]]
            .loans[x["Loan ID"]]
            .collateral,
            prices=prices.prices,
        ),
        axis=1,
    )
    hashstack_loan_stats['Collateral'] = hashstack_loan_stats.apply(
        lambda x: src.hashstack.get_collateral_str(loan = hashstack_state.user_states[x['User']].loans[x['Loan ID']]),
        axis = 1,
    )
    hashstack_loan_stats["Borrowings"] = hashstack_loan_stats.apply(
        lambda x: (
            str(
                hashstack_state.user_states[x["User"]]
                .loans[x["Loan ID"]]
                .borrowings.market
            )
            + ": "
            + str(
                format(
                    hashstack_state.user_states[x["User"]]
                    .loans[x["Loan ID"]]
                    .borrowings.amount
                    / (
                        src.constants.TOKEN_DECIMAL_FACTORS[
                            hashstack_state.user_states[x["User"]]
                            .loans[x["Loan ID"]]
                            .borrowings.market
                        ]
                    ),
                    ".4f",
                )
            )
        ),
        axis=1,
    )
    hashstack_loan_stats.drop(columns=["Loan ID"], inplace=True)
    hashstack_loan_stats.loc[
        hashstack_loan_stats["Borrowing in USD"] >= decimal.Decimal("100")
    ].sort_values("Health factor").iloc[:20].to_csv(
        "hashstack_data/large_loans_sample.csv", index=False
    )
    hashstack_loan_stats.loc[
        hashstack_loan_stats["Borrowing in USD"] < decimal.Decimal("100")
    ].sort_values("Health factor").iloc[:20].to_csv(
        "hashstack_data/small_loans_sample.csv", index=False
    )

    nostra_loan_stats = pandas.DataFrame()
    nostra_loan_stats["User"] = [
        user
        for user in nostra_state.user_states.keys()
    ]
    nostra_loan_stats["Protocol"] = "Nostra"
    nostra_loan_stats["Borrowing in USD"] = nostra_loan_stats.apply(
        lambda x: src.nostra.compute_borrowings_amount_usd(
            user_state=nostra_state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    nostra_loan_stats[
        "Risk adjusted collateral in USD"
    ] = nostra_loan_stats.apply(
        lambda x: src.nostra.compute_risk_adjusted_collateral_usd(
            user_state=nostra_state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    nostra_loan_stats["Health factor"] = nostra_loan_stats.apply(
        lambda x: src.nostra.compute_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            risk_adjusted_debt_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )
    nostra_loan_stats["Standardized health factor"] = nostra_loan_stats.apply(
        lambda x: src.nostra.compute_standardized_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            borrowings_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )
    nostra_loan_stats["Collateral"] = nostra_loan_stats.apply(
        lambda x: ''.join(
            f"{token}: {round((token_state.collateral + token_state.interest_bearing_collateral) / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}, "
            for token, token_state
            in nostra_state.user_states[x["User"]].token_states.items()
            if (
                token_state.collateral > 0
                or token_state.interest_bearing_collateral > 0
            )
        ),
        axis=1,
    )
    nostra_loan_stats["Borrowings"] = nostra_loan_stats.apply(
        lambda x: ''.join(
            f"{token}: {round(token_state.debt / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}, "
            for token, token_state
            in nostra_state.user_states[x["User"]].token_states.items()
            if token_state.debt > 0
        ),
        axis=1,
    )
    nostra_loan_stats.loc[
        nostra_loan_stats["Borrowing in USD"] >= decimal.Decimal("100")
    ].sort_values("Health factor").iloc[:20].to_csv(
        "nostra_data/large_loans_sample.csv", index=False
    )
    nostra_loan_stats.loc[
        nostra_loan_stats["Borrowing in USD"] < decimal.Decimal("100")
    ].sort_values("Health factor").iloc[:20].to_csv(
        "nostra_data/small_loans_sample.csv", index=False
    )

    general_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
            ],
            'Number of users': [
                len(zklend_loan_stats),
                len(hashstack_loan_stats),
                len(nostra_loan_stats),
            ],
            'Total debt in USD': [
                round(zklend_loan_stats['Borrowing in USD'].sum(), 4),
                round(hashstack_loan_stats['Borrowing in USD'].sum(), 4),
                round(nostra_loan_stats['Borrowing in USD'].sum(), 4),
            ],
            'Total risk adjusted collateral in USD': [
                round(zklend_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
                round(hashstack_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
                round(nostra_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
            ],
        },
    )
    general_stats.to_csv("general_stats.csv", index=False)

    zklend_eth_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_eth_supply = decimal.Decimal(str(zklend_eth_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
    zklend_wbtc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_wbtc_supply = decimal.Decimal(str(zklend_wbtc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC']
    zklend_usdc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_usdc_supply = decimal.Decimal(str(zklend_usdc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDC']
    zklend_dai_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_dai_supply = decimal.Decimal(str(zklend_dai_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['DAI']
    zklend_usdt_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_usdt_supply = decimal.Decimal(str(zklend_usdt_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDT']

    hashstack_eth_supply = asyncio.run(
        src.blockchain_call.balance_of(
            token_addr = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
            holder_addr = '0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e',
        )
    )
    hashstack_eth_supply = decimal.Decimal(str(hashstack_eth_supply)) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
    hashstack_wbtc_supply = asyncio.run(
        src.blockchain_call.balance_of(
            token_addr = '0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac',
            holder_addr = '0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e',
        )
    )
    hashstack_wbtc_supply = decimal.Decimal(str(hashstack_wbtc_supply)) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC']
    hashstack_usdc_supply = asyncio.run(
        src.blockchain_call.balance_of(
            token_addr = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
            holder_addr = '0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e',
        )
    )
    hashstack_usdc_supply = decimal.Decimal(str(hashstack_usdc_supply)) / src.constants.TOKEN_DECIMAL_FACTORS['USDC']
    hashstack_dai_supply = asyncio.run(
        src.blockchain_call.balance_of(
            token_addr = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
            holder_addr = '0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e',
        )
    )
    hashstack_dai_supply = decimal.Decimal(str(hashstack_dai_supply)) / src.constants.TOKEN_DECIMAL_FACTORS['DAI']
    hashstack_usdt_supply = asyncio.run(
        src.blockchain_call.balance_of(
            token_addr = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
            holder_addr = '0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e',
        )
    )
    hashstack_usdt_supply = decimal.Decimal(str(hashstack_usdt_supply)) / src.constants.TOKEN_DECIMAL_FACTORS['USDT']

    nostra_eth_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_eth_supply = decimal.Decimal(str(nostra_eth_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
    nostra_wbtc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_wbtc_supply = decimal.Decimal(str(nostra_wbtc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC']
    nostra_usdc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_usdc_supply = decimal.Decimal(str(nostra_usdc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDC']
    nostra_dai_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_dai_supply = decimal.Decimal(str(nostra_dai_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['DAI']
    nostra_usdt_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_usdt_supply = decimal.Decimal(str(nostra_usdt_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDT']
    supply_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
            ],
            'ETH supply': [
                round(zklend_eth_supply, 4),
                round(hashstack_eth_supply, 4),
                round(nostra_eth_supply, 4),
            ],
            'wBTC supply': [
                round(zklend_wbtc_supply, 4),
                round(hashstack_wbtc_supply, 4),
                round(nostra_wbtc_supply, 4),
            ],
            'USDC supply': [
                round(zklend_usdc_supply, 4),
                round(hashstack_usdc_supply, 4),
                round(nostra_usdc_supply, 4),
            ],
            'DAI supply': [
                round(zklend_dai_supply, 4),
                round(hashstack_dai_supply, 4),
                round(nostra_dai_supply, 4),
            ],
            'USDT supply': [
                round(zklend_usdt_supply, 4),
                round(hashstack_usdt_supply, 4),
                round(nostra_usdt_supply, 4),
            ],
        }
    )
    supply_stats['Total supply in USD'] = (
        supply_stats['ETH supply'] * prices.prices['ETH']
        + supply_stats['wBTC supply'] * prices.prices['wBTC']
        + supply_stats['USDC supply'] * prices.prices['USDC']
        + supply_stats['DAI supply'] * prices.prices['DAI']
        + supply_stats['USDT supply'] * prices.prices['USDT']
    ).astype(float).round(4)
    supply_stats.to_csv("supply_stats.csv", index=False)

    collateral_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
            ],
            'ETH collateral': [
                round(sum(x.token_states['ETH'].deposit * x.token_states['ETH'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'ETH') / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].collateral + x.token_states['ETH'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
            ],
            'wBTC collateral': [
                round(sum(x.token_states['wBTC'].deposit * x.token_states['wBTC'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'wBTC') / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].collateral + x.token_states['wBTC'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
            ],
            'USDC collateral': [
                round(sum(x.token_states['USDC'].deposit * x.token_states['USDC'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'USDC') / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].collateral + x.token_states['USDC'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
            ],
            'DAI collateral': [
                round(sum(x.token_states['DAI'].deposit * x.token_states['DAI'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'DAI') / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].collateral + x.token_states['DAI'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
            ],
            'USDT collateral': [
                round(sum(x.token_states['USDT'].deposit * x.token_states['USDT'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'USDT') / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].collateral + x.token_states['USDT'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
            ],
        },
    )
    collateral_stats.to_csv("collateral_stats.csv", index=False)

    debt_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
            ],
            'ETH debt': [
                round(sum(x.token_states['ETH'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'ETH') / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
            ],
            'wBTC debt': [
                round(sum(x.token_states['wBTC'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'wBTC') / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
            ],
            'USDC debt': [
                round(sum(x.token_states['USDC'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'USDC') / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
            ],
            'DAI debt': [
                round(sum(x.token_states['DAI'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'DAI') / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
            ],
            'USDT debt': [
                round(sum(x.token_states['USDT'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'USDT') / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
            ],
        },
    )
    debt_stats.to_csv("debt_stats.csv", index=False)

    max_block_number = zklend_events["block_number"].max()
    max_timestamp = zklend_events["timestamp"].max()

    dict = {"timestamp": str(max_timestamp),
            "block_number": str(max_block_number)}

    with open("data/last_update.json", "w") as outfile:
        outfile.write(json.dumps(dict))

    print(f"Updated CSV data in {time.time() - t0}s", flush=True)
    return state


def update_data_continuously():
    state = src.persistent_state.download_and_load_state_from_pickle()
    while True:
        state = update_data(state)
        src.persistent_state.upload_state_as_pickle(state)
        print("DATA UPDATED", flush=True)
        time.sleep(120)


if __name__ == "__main__":
    update_data(src.zklend.State())
