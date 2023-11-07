import asyncio
import decimal
import json
import time

import pandas

import src.constants
import src.db
import src.hashstack
import src.nostra
import src.nostra_uncapped
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
    c, b = pair.split("-")
    data = generate_graph_data(state, prices, swap_amm, c, b)
    filename = f"data/{c}-{b}.csv"
    data.to_csv(filename, index=False, compression='gzip')
    print(filename, "done in", time.time() - t0, flush=True)


def get_events(block_number) -> pandas.DataFrame:
    connection = src.db.establish_connection()
    relevant_events = tuple(src.zklend.EVENTS_METHODS_MAPPING)
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{src.constants.Protocol.ZKLEND.value}'
      AND
          key_name IN {relevant_events}
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
    nostra_uncapped_events = src.nostra_uncapped.get_nostra_events()
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

    nostra_uncapped_state = src.nostra_uncapped.State()
    for _, nostra_uncapped_event in nostra_uncapped_events.iterrows():
        nostra_uncapped_state.process_event(event=nostra_uncapped_event)

    print(f"updated state in {time.time() - t1}s", flush=True)

    t_prices = time.time()
    prices = src.swap_liquidity.Prices()

    print(f"prices in {time.time() - t_prices}s", flush=True)

    t_swap = time.time()

    swap_amms = asyncio.run(src.swap_liquidity.SwapAmm().init())

    print(f"swap in {time.time() - t_swap}s", flush=True)

    t2 = time.time()

    [generate_and_store_graph_data(
        state, prices, swap_amms, pair) for pair in src.constants.PAIRS]
    [
        src.hashstack.generate_and_store_graph_data(
            hashstack_state, prices, swap_amms, pair)
        for pair in src.constants.PAIRS
    ]
    [
        src.nostra.generate_and_store_graph_data(
            nostra_state, prices, swap_amms, pair)
        for pair in src.constants.PAIRS
    ]
    [
        src.nostra_uncapped.generate_and_store_graph_data(
            nostra_uncapped_state, prices, swap_amms, pair)
        for pair in src.constants.PAIRS
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
        if (token[0] != "z" and token != 'wstETH')  # TODO: add wstETH
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
        if (token[0] != "z" and token != 'wstETH')  # wstETH is only available for zkLend
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
        if (token[0] != "z" and token != 'wstETH')  # wstETH is only available for zkLend
    ]
    nostra_uncapped_histogram_data = [
        {
            "token": token,
            "borrowings": user_state.token_states[token].debt
            * prices.prices[token]
            / 10 ** src.constants.get_decimals(token),
        }
        for user_state in nostra_uncapped_state.user_states.values()
        for token in src.constants.symbol_decimals_map.keys()
        if (token[0] != "z" and token != 'wstETH')  # wstETH is only available for zkLend
    ]

    pandas.DataFrame(histogram_data).to_csv("data/histogram.csv", index=False, compression='gzip')
    pandas.DataFrame(hashstack_histogram_data).to_csv(
        "hashstack_data/histogram.csv", index=False, compression='gzip'
    )
    pandas.DataFrame(nostra_histogram_data).to_csv(
        "nostra_data/histogram.csv", index=False, compression='gzip'
    )
    pandas.DataFrame(nostra_uncapped_histogram_data).to_csv(
        "nostra_uncapped_data/histogram.csv", index=False, compression='gzip'
    )

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
    zklend_loan_stats["Collateral"] = zklend_loan_stats.apply(
        lambda x: ', '.join(
            f"{token}: {round(token_state.deposit * token_state.collateral_enabled / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_state
            in state.user_states[x["User"]].token_states.items()
            if (not token_state.z_token and token_state.deposit * token_state.collateral_enabled > 0)
        ),
        axis=1,
    )
    zklend_loan_stats["Borrowings"] = zklend_loan_stats.apply(
        lambda x: ', '.join(
            f"{token}: {round(token_state.borrowings / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_state
            in state.user_states[x["User"]].token_states.items()
            if (not token_state.z_token and token_state.borrowings > 0)
        ),
        axis=1,
    )
    zklend_loan_stats.to_csv("data/loans.csv", index=False, compression='gzip')

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
    hashstack_loan_stats.to_csv("hashstack_data/loans.csv", index=False, compression='gzip')

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
        lambda x: ', '.join(
            f"{token}: {round((token_state.collateral + token_state.interest_bearing_collateral) / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
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
        lambda x: ', '.join(
            f"{token}: {round(token_state.debt / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_state
            in nostra_state.user_states[x["User"]].token_states.items()
            if token_state.debt > 0
        ),
        axis=1,
    )
    nostra_loan_stats.to_csv("nostra_data/loans.csv", index=False, compression='gzip')

    nostra_uncapped_loan_stats = pandas.DataFrame()
    nostra_uncapped_loan_stats["User"] = [
        user
        for user in nostra_uncapped_state.user_states.keys()
    ]
    nostra_uncapped_loan_stats["Protocol"] = "Nostra uncapped"
    nostra_uncapped_loan_stats["Borrowing in USD"] = nostra_uncapped_loan_stats.apply(
        lambda x: src.nostra_uncapped.compute_borrowings_amount_usd(
            user_state=nostra_uncapped_state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats[
        "Risk adjusted collateral in USD"
    ] = nostra_uncapped_loan_stats.apply(
        lambda x: src.nostra_uncapped.compute_risk_adjusted_collateral_usd(
            user_state=nostra_uncapped_state.user_states[x["User"]],
            prices=prices.prices,
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats["Health factor"] = nostra_uncapped_loan_stats.apply(
        lambda x: src.nostra_uncapped.compute_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            risk_adjusted_debt_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats["Standardized health factor"] = nostra_uncapped_loan_stats.apply(
        lambda x: src.nostra_uncapped.compute_standardized_health_factor(
            risk_adjusted_collateral_usd=x["Risk adjusted collateral in USD"],
            borrowings_usd=x["Borrowing in USD"],
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats["Collateral"] = nostra_uncapped_loan_stats.apply(
        lambda x: ', '.join(
            f"{token}: {round((token_state.collateral + token_state.interest_bearing_collateral) / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_state
            in nostra_uncapped_state.user_states[x["User"]].token_states.items()
            if (
                token_state.collateral > 0
                or token_state.interest_bearing_collateral > 0
            )
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats["Borrowings"] = nostra_uncapped_loan_stats.apply(
        lambda x: ', '.join(
            f"{token}: {round(token_state.debt / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_state
            in nostra_uncapped_state.user_states[x["User"]].token_states.items()
            if token_state.debt > 0
        ),
        axis=1,
    )
    nostra_uncapped_loan_stats.to_csv("nostra_uncapped_data/loans.csv", index=False, compression='gzip')

    general_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
                'Nostra uncapped',
            ],
            'Number of users': [
                src.zklend.compute_number_of_users(state),
                src.hashstack.compute_number_of_users(hashstack_state),
                src.nostra.compute_number_of_users(nostra_state),
                src.nostra_uncapped.compute_number_of_users(nostra_uncapped_state),
            ],
            'Number of stakers': [
                src.zklend.compute_number_of_stakers(state),
                src.hashstack.compute_number_of_stakers(hashstack_state),
                src.nostra.compute_number_of_stakers(nostra_state),
                src.nostra_uncapped.compute_number_of_stakers(nostra_uncapped_state),
            ],
            'Number of borrowers': [
                src.zklend.compute_number_of_borrowers(state),
                src.hashstack.compute_number_of_borrowers(hashstack_state),
                src.nostra.compute_number_of_borrowers(nostra_state),
                src.nostra_uncapped.compute_number_of_borrowers(nostra_uncapped_state),
            ],
            # Hashstack is the only protocol for which the number of loans doesn't equal the number of borrowers. The reason is
            # that Hashstack allows for liquidations on the loan level, whereas other protocols use user-level liquidations.
            'Number of loans': [
                src.zklend.compute_number_of_borrowers(state),
                src.hashstack.compute_number_of_loans(hashstack_state),
                src.nostra.compute_number_of_borrowers(nostra_state),
                src.nostra_uncapped.compute_number_of_borrowers(nostra_uncapped_state),
            ],
            'Total debt in USD': [
                round(zklend_loan_stats['Borrowing in USD'].sum(), 4),
                round(hashstack_loan_stats['Borrowing in USD'].sum(), 4),
                round(nostra_loan_stats['Borrowing in USD'].sum(), 4),
                round(nostra_uncapped_loan_stats['Borrowing in USD'].sum(), 4),
            ],
            'Total risk adjusted collateral in USD': [
                round(zklend_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
                round(hashstack_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
                round(nostra_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
                round(nostra_uncapped_loan_stats['Risk adjusted collateral in USD'].sum(), 4),
            ],
        },
    )
    general_stats.to_csv("general_stats.csv", index=False, compression='gzip')

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
    zklend_wsteth_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x0536aa7e01ecc0235ca3e29da7b5ad5b12cb881e29034d87a4290edbb20b7c28', base=16),
            selector = 'felt_total_supply',
            calldata = [],
        )
    )
    zklend_wsteth_supply = decimal.Decimal(str(zklend_wsteth_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['wstETH']

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
    hashstack_wsteth_supply = decimal.Decimal("0")

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
    nostra_wsteth_supply = decimal.Decimal("0")

    nostra_uncapped_eth_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_uncapped_eth_supply = decimal.Decimal(str(nostra_uncapped_eth_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
    nostra_uncapped_wbtc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_uncapped_wbtc_supply = decimal.Decimal(str(nostra_uncapped_wbtc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC']
    nostra_uncapped_usdc_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_uncapped_usdc_supply = decimal.Decimal(str(nostra_uncapped_usdc_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDC']
    nostra_uncapped_dai_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_uncapped_dai_supply = decimal.Decimal(str(nostra_uncapped_dai_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['DAI']
    nostra_uncapped_usdt_supply = asyncio.run(
        src.blockchain_call.func_call(
            addr = int('0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83', base=16),
            selector = 'totalSupply',
            calldata = [],
        )
    )
    nostra_uncapped_usdt_supply = decimal.Decimal(str(nostra_uncapped_usdt_supply[0])) / src.constants.TOKEN_DECIMAL_FACTORS['USDT']
    nostra_uncapped_wsteth_supply = decimal.Decimal("0")

    supply_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
                'Nostra uncapped',
            ],
            'ETH supply': [
                round(zklend_eth_supply, 4),
                round(hashstack_eth_supply, 4),
                round(nostra_eth_supply, 4),
                round(nostra_uncapped_eth_supply, 4),
            ],
            'wBTC supply': [
                round(zklend_wbtc_supply, 4),
                round(hashstack_wbtc_supply, 4),
                round(nostra_wbtc_supply, 4),
                round(nostra_uncapped_wbtc_supply, 4),
            ],
            'USDC supply': [
                round(zklend_usdc_supply, 4),
                round(hashstack_usdc_supply, 4),
                round(nostra_usdc_supply, 4),
                round(nostra_uncapped_usdc_supply, 4),
            ],
            'DAI supply': [
                round(zklend_dai_supply, 4),
                round(hashstack_dai_supply, 4),
                round(nostra_dai_supply, 4),
                round(nostra_uncapped_dai_supply, 4),
            ],
            'USDT supply': [
                round(zklend_usdt_supply, 4),
                round(hashstack_usdt_supply, 4),
                round(nostra_usdt_supply, 4),
                round(nostra_uncapped_usdt_supply, 4),
            ],
            'wstETH supply': [
                round(zklend_wsteth_supply, 4),
                round(hashstack_wsteth_supply, 4),
                round(nostra_wsteth_supply, 4),
            ],
        }
    )
    supply_stats['Total supply in USD'] = (
        supply_stats['ETH supply'] * prices.prices['ETH']
        + supply_stats['wBTC supply'] * prices.prices['wBTC']
        + supply_stats['USDC supply'] * prices.prices['USDC']
        + supply_stats['DAI supply'] * prices.prices['DAI']
        + supply_stats['USDT supply'] * prices.prices['USDT']
        + supply_stats['wstETH supply'] * prices.prices['wstETH']
    ).apply(lambda x: round(x, 4))
    supply_stats.to_csv("supply_stats.csv", index=False, compression='gzip')

    collateral_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
                'Nostra uncapped',
            ],
            'ETH collateral': [
                round(sum(x.token_states['ETH'].deposit * x.token_states['ETH'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'ETH') / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].collateral + x.token_states['ETH'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].collateral + x.token_states['ETH'].interest_bearing_collateral for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
            ],
            'wBTC collateral': [
                round(sum(x.token_states['wBTC'].deposit * x.token_states['wBTC'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'wBTC') / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].collateral + x.token_states['wBTC'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].collateral + x.token_states['wBTC'].interest_bearing_collateral for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
            ],
            'USDC collateral': [
                round(sum(x.token_states['USDC'].deposit * x.token_states['USDC'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'USDC') / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].collateral + x.token_states['USDC'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].collateral + x.token_states['USDC'].interest_bearing_collateral for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
            ],
            'DAI collateral': [
                round(sum(x.token_states['DAI'].deposit * x.token_states['DAI'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'DAI') / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].collateral + x.token_states['DAI'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].collateral + x.token_states['DAI'].interest_bearing_collateral for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
            ],
            'USDT collateral': [
                round(sum(x.token_states['USDT'].deposit * x.token_states['USDT'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(loan.collateral.current_amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.collateral.market == 'USDT') / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].collateral + x.token_states['USDT'].interest_bearing_collateral for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].collateral + x.token_states['USDT'].interest_bearing_collateral for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
            ],
            'wstETH collateral': [
                round(sum(x.token_states['wstETH'].deposit * x.token_states['wstETH'].collateral_enabled for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wstETH'], 4),
                round(decimal.Decimal("0"), 4),
                round(decimal.Decimal("0"), 4),
            ],
        },
    )
    collateral_stats.to_csv("collateral_stats.csv", index=False, compression='gzip')

    debt_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
                'Nostra uncapped',
            ],
            'ETH debt': [
                round(sum(x.token_states['ETH'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'ETH') / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
                round(sum(x.token_states['ETH'].debt for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['ETH'], 4),
            ],
            'wBTC debt': [
                round(sum(x.token_states['wBTC'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'wBTC') / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
                round(sum(x.token_states['wBTC'].debt for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wBTC'], 4),
            ],
            'USDC debt': [
                round(sum(x.token_states['USDC'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'USDC') / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
                round(sum(x.token_states['USDC'].debt for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDC'], 4),
            ],
            'DAI debt': [
                round(sum(x.token_states['DAI'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'DAI') / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
                round(sum(x.token_states['DAI'].debt for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['DAI'], 4),
            ],
            'USDT debt': [
                round(sum(x.token_states['USDT'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(loan.borrowings.amount for user_state in hashstack_state.user_states.values() for loan in user_state.loans.values() if loan.borrowings.market == 'USDT') / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].debt for x in nostra_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
                round(sum(x.token_states['USDT'].debt for x in nostra_uncapped_state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['USDT'], 4),
            ],
            'wstETH debt': [
                round(sum(x.token_states['wstETH'].borrowings for x in state.user_states.values()) / src.constants.TOKEN_DECIMAL_FACTORS['wstETH'], 4),
                round(decimal.Decimal("0"), 4),
                round(decimal.Decimal("0"), 4),
            ],
        },
    )
    debt_stats.to_csv("debt_stats.csv", index=False, compression='gzip')

    utilization_stats = pandas.DataFrame(
        {
            'Protocol': [
                'zkLend',
                'Hashstack',
                'Nostra',
                'Nostra uncapped',
            ],
            'Total utilization': general_stats['Total debt in USD'] / (general_stats['Total debt in USD'] + supply_stats['Total supply in USD']),
            'ETH utilization': debt_stats['ETH debt'] / (supply_stats['ETH supply'] + debt_stats['ETH debt']),
            'wBTC utilization': debt_stats['wBTC debt'] / (supply_stats['wBTC supply'] + debt_stats['wBTC debt']),
            'USDC utilization': debt_stats['USDC debt'] / (supply_stats['USDC supply'] + debt_stats['USDC debt']),
            'DAI utilization': debt_stats['DAI debt'] / (supply_stats['DAI supply'] + debt_stats['DAI debt']),
            'USDT utilization': debt_stats['USDT debt'] / (supply_stats['USDT supply'] + debt_stats['USDT debt']),
            # TODO: hotfix to avoid `InvalidOperation: [<class 'decimal.DivisionUndefined'>]`
            'wstETH utilization': debt_stats['wstETH debt'].astype(float) / (supply_stats['wstETH supply'].astype(float) + debt_stats['wstETH debt'].astype(float)),
        },
    )
    utilization_columns = [x for x in utilization_stats.columns if 'utilization' in x]
    utilization_stats[utilization_columns] = utilization_stats[utilization_columns].applymap(lambda x: round(x, 4))
    utilization_stats.to_csv("utilization_stats.csv", index=False, compression='gzip')

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
