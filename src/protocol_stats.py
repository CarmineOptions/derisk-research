import asyncio
import collections

import pandas

import src.blockchain_call
import src.hashstack_v0
import src.hashstack_v1
import src.helpers
import src.main_chart
import src.protocol_parameters
import src.settings
import src.state
import src.types


def get_general_stats(
    states: list[src.state.State],
    loan_stats: dict[str, pandas.DataFrame],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        if (
            isinstance(state, src.hashstack_v0.HashstackV0State)
            or isinstance(state, src.hashstack_v1.HashstackV1State)
        ):
            number_of_active_users = state.compute_number_of_active_users()
            number_of_active_borrowers = state.compute_number_of_active_borrowers()
        else:
            number_of_active_users = state.compute_number_of_active_loan_entities()
            number_of_active_borrowers = state.compute_number_of_active_loan_entities_with_debt()
        data.append(
            {
                'Protocol': protocol,
                'Number of active users': number_of_active_users,
                # At the moment, Hashstack V0 and Hashstack V1 are the only protocols for which the number of active 
                # loans doesn't equal the number of active users. The reason is that Hashstack V0 and Hashstack V1 
                # allow for liquidations on the loan level, whereas other protocols use user-level liquidations.
                'Number of active loans': state.compute_number_of_active_loan_entities(),
                'Number of active borrowers': number_of_active_borrowers,
                'Total debt (USD)': round(loan_stats[protocol]['Debt (USD)'].sum(), 4),
                'Total risk adjusted collateral (USD)': round(loan_stats[protocol]['Risk-adjusted collateral (USD)'].sum(), 4),
                'Total Collateral (USD)': round(loan_stats[protocol]['Collateral (USD)'].sum(), 4),
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        path = "data/general_stats.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data


def get_supply_stats(
    states: list[src.state.State],
    prices: src.types.Prices,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_supplies = {}
        for token in src.settings.TOKEN_SETTINGS:
            if protocol == 'Hashstack V0':
                supply = asyncio.run(
                    src.blockchain_call.balance_of(
                        token_addr = src.settings.TOKEN_SETTINGS[token].address,
                        holder_addr = src.hashstack_v0.ADDRESS,
                    )
                )
            elif protocol == 'Hashstack V1':
                supply = asyncio.run(
                    src.blockchain_call.balance_of(
                        token_addr = src.settings.TOKEN_SETTINGS[token].address,
                        holder_addr = src.hashstack_v1.R_TOKENS[token],
                    )
                )
            # TODO: zkLend, Nostra Alpha and Nostra Mainnet should be implemented similarly to Hashstack V0 and V1.
            else:
                addresses, selector = src.protocol_parameters.get_supply_function_call_parameters(
                    protocol=protocol, 
                    token_addresses=src.helpers.get_addresses(
                        token_parameters=state.token_parameters.collateral,
                        underlying_symbol=token,
                    ),
                )
                supply = 0
                for address in addresses:
                    supply += asyncio.run(
                        src.blockchain_call.func_call(
                            addr = int(address, base=16),
                            selector = selector,
                            calldata = [],
                        )
                    )[0]
            supply = supply / src.settings.TOKEN_SETTINGS[token].decimal_factor
            token_supplies[token] = round(supply, 4)
        data.append(
            {
                'Protocol': protocol,
                'ETH supply': token_supplies['ETH'],
                'WBTC supply': token_supplies['WBTC'],
                'USDC supply': token_supplies['USDC'],
                'DAI supply': token_supplies['DAI'],
                'USDT supply': token_supplies['USDT'],
                'wstETH supply': token_supplies['wstETH'],
                'LORDS supply': token_supplies['LORDS'],
                'STRK supply': token_supplies['STRK'],
            }
        )
    data = pandas.DataFrame(data)
    data['Total supply (USD)'] = sum(
        data[column] * prices[src.settings.TOKEN_SETTINGS[column.replace(' supply', '')].address]
        for column in data.columns 
        if 'supply' in column
    ).apply(lambda x: round(x, 4))
    if save_data:
        path = "data/supply_stats.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data


def get_collateral_stats(
    states: list[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_collaterals = collections.defaultdict(float)
        for token in src.settings.TOKEN_SETTINGS:
            # TODO: save zkLend amounts under token_addresses?
            if protocol == 'zkLend':
                token_addresses = [
                    src.helpers.get_underlying_address(
                        token_parameters=state.token_parameters.collateral,
                        underlying_symbol=token,
                    )
                ]
            elif protocol in {'Nostra Alpha', 'Nostra Mainnet'}:
                token_addresses = src.helpers.get_addresses(
                    token_parameters=state.token_parameters.collateral,
                    underlying_symbol=token,
                )
            else:
                raise ValueError
            for token_address in token_addresses:
                collateral = (
                    sum(
                        float(loan_entity.collateral[token_address])
                        for loan_entity in state.loan_entities.values()
                    )
                    / src.settings.TOKEN_SETTINGS[token].decimal_factor
                    * float(state.interest_rate_models.collateral[token_address])
                )
                token_collaterals[token] += round(collateral, 4)

        data.append(
            {
                'Protocol': protocol,
                'ETH collateral': token_collaterals['ETH'],
                'WBTC collateral': token_collaterals['WBTC'],
                'USDC collateral': token_collaterals['USDC'],
                'DAI collateral': token_collaterals['DAI'],
                'USDT collateral': token_collaterals['USDT'],
                'wstETH collateral': token_collaterals['wstETH'],
                'LORDS collateral': token_collaterals['LORDS'],
                'STRK collateral': token_collaterals['STRK'],
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        path = "data/collateral_stats.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data


def get_debt_stats(
    states: list[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_debts = collections.defaultdict(float)
        for token in src.settings.TOKEN_SETTINGS:
            # TODO: save zkLend amounts under token_addresses?
            if protocol == 'zkLend':
                token_addresses = [
                        src.helpers.get_underlying_address(
                        token_parameters=state.token_parameters.debt,
                        underlying_symbol=token,
                    )
                ]
            elif protocol in {'Nostra Alpha', 'Nostra Mainnet'}:
                token_addresses = src.helpers.get_addresses(
                    token_parameters=state.token_parameters.debt,
                    underlying_symbol=token,
                )
            else:
                raise ValueError
            for token_address in token_addresses:
                debt = (
                    sum(
                        float(loan_entity.debt[token_address])
                        for loan_entity in state.loan_entities.values()
                    )
                    / src.settings.TOKEN_SETTINGS[token].decimal_factor
                    * float(state.interest_rate_models.debt[token_address])
                )
                token_debts[token] = round(debt, 4)

        data.append(
            {
                'Protocol': protocol,
                'ETH debt': token_debts['ETH'],
                'WBTC debt': token_debts['WBTC'],
                'USDC debt': token_debts['USDC'],
                'DAI debt': token_debts['DAI'],
                'USDT debt': token_debts['USDT'],
                'wstETH debt': token_debts['wstETH'],
                'LORDS debt': token_debts['LORDS'],
                'STRK debt': token_debts['STRK'],
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        path = "data/debt_stats.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data


def get_utilization_stats(
    general_stats: pandas.DataFrame,
    supply_stats: pandas.DataFrame,
    debt_stats: pandas.DataFrame,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = pandas.DataFrame(
        {
            'Protocol': general_stats['Protocol'],
            'Total utilization': general_stats['Total debt (USD)'] / (
                general_stats['Total debt (USD)'] + supply_stats['Total supply (USD)']
            ),
            'ETH utilization': debt_stats['ETH debt'] / (supply_stats['ETH supply'] + debt_stats['ETH debt']),
            'WBTC utilization': debt_stats['WBTC debt'] / (supply_stats['WBTC supply'] + debt_stats['WBTC debt']),
            'USDC utilization': debt_stats['USDC debt'] / (supply_stats['USDC supply'] + debt_stats['USDC debt']),
            'DAI utilization': debt_stats['DAI debt'] / (supply_stats['DAI supply'] + debt_stats['DAI debt']),
            'USDT utilization': debt_stats['USDT debt'] / (supply_stats['USDT supply'] + debt_stats['USDT debt']),
            'wstETH utilization': debt_stats['wstETH debt'] / (supply_stats['wstETH supply'] + debt_stats['wstETH debt']),
            'LORDS utilization': debt_stats['LORDS debt'] / (supply_stats['LORDS supply'] + debt_stats['LORDS debt']),
            'STRK utilization': debt_stats['STRK debt'] / (supply_stats['STRK supply'] + debt_stats['STRK debt']),
        },
    )
    utilization_columns = [x for x in data.columns if 'utilization' in x]
    data[utilization_columns] = data[utilization_columns].map(lambda x: round(x, 4))
    if save_data:
        path = "data/utilization_stats.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data