from typing import Dict, List
import asyncio
import decimal
import pandas

import src.blockchain_call
import src.constants
import src.helpers
import src.state



def get_general_stats(
    states: List[src.state.State],
    loan_stats: Dict[str, pandas.DataFrame],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.helpers.get_protocol(state=state)
        if isinstance(state, src.hashstack.HashstackState):
            number_of_active_users = state.compute_number_of_active_users()
            number_of_active_borrowers = state.compute_number_of_active_borrowers()
        else:
            number_of_active_users = state.compute_number_of_active_loan_entities()
            number_of_active_borrowers = state.compute_number_of_active_loan_entities_with_debt()
        data.append(
            {
                'Protocol': protocol,
                'Number of active users': number_of_active_users,
                # At the moment, Hashstack is the only protocol for which the number of active loans doesn't equal the 
                # number of active users. The reason is that Hashstack allows for liquidations on the loan level, 
                # whereas other protocols use user-level liquidations.
                'Number of active loans': state.compute_number_of_active_loan_entities(),
                'Number of active borrowers': number_of_active_borrowers,
                'Total debt (USD)': round(loan_stats[protocol]['Debt (USD)'].sum(), 4),
                'Total risk adjusted collateral (USD)': round(loan_stats[protocol]['Risk-adjusted collateral (USD)'].sum(), 4),
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        data.to_csv("data/general_stats.csv", index=False, compression='gzip')
    return data


def get_supply_stats(
    states: List[src.state.State],
    prices: Dict[str, decimal.Decimal],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.helpers.get_protocol(state=state)
        token_supplies = {}
        for token in src.constants.TOKEN_DECIMAL_FACTORS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_supplies[token] = decimal.Decimal("0")
                continue
            if protocol == 'Hashstack':
                token_address, holder_address = src.helpers.get_hashstack_supply_parameters(token=token)
                supply = asyncio.run(
                    src.blockchain_call.balance_of(
                        token_addr = token_address,
                        holder_addr = holder_address,
                    )
                )
            else:
                address, selector = src.helpers.get_supply_function_call_parameters(protocol=protocol, token=token)
                supply = asyncio.run(
                    src.blockchain_call.func_call(
                        addr = int(address, base=16),
                        selector = selector,
                        calldata = [],
                    )
                )[0]
            supply = decimal.Decimal(str(supply)) / src.constants.TOKEN_DECIMAL_FACTORS[token]
            token_supplies[token] = round(supply, 4)
        data.append(
            {
                'Protocol': protocol,
                'ETH supply': token_supplies['ETH'],
                'wBTC supply': token_supplies['wBTC'],
                'USDC supply': token_supplies['USDC'],
                'DAI supply': token_supplies['DAI'],
                'USDT supply': token_supplies['USDT'],
                'wstETH supply': token_supplies['wstETH'],
            }
        )
    data = pandas.DataFrame(data)
    data['Total supply (USD)'] = sum(
        data[column] * prices[column.split(' ')[0]] 
        for column in data.columns 
        if 'supply' in column
    ).apply(lambda x: round(x, 4))
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        data.to_csv("data/supply_stats.csv", index=False, compression='gzip')
    return data


def get_collateral_stats(
    states: List[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.helpers.get_protocol(state=state)
        token_collaterals = {}
        for token in src.constants.TOKEN_DECIMAL_FACTORS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_collaterals[token] = decimal.Decimal("0")
                continue
            collateral = sum(
                loan_entity.collateral.token_amounts[token]
                for loan_entity in state.loan_entities.values()
            ) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
            token_collaterals[token] = round(collateral, 4)
        data.append(
            {
                'Protocol': protocol,
                'ETH collateral': token_collaterals['ETH'],
                'wBTC collateral': token_collaterals['wBTC'],
                'USDC collateral': token_collaterals['USDC'],
                'DAI collateral': token_collaterals['DAI'],
                'USDT collateral': token_collaterals['USDT'],
                'wstETH collateral': token_collaterals['wstETH'],
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        data.to_csv("data/collateral_stats.csv", index=False, compression='gzip')
    return data


def get_debt_stats(
    states: List[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.helpers.get_protocol(state=state)
        token_debts = {}
        for token in src.constants.TOKEN_DECIMAL_FACTORS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_debts[token] = decimal.Decimal("0")
                continue
            debt = sum(
                loan_entity.debt.token_amounts[token]
                for loan_entity in state.loan_entities.values()
            ) / src.constants.TOKEN_DECIMAL_FACTORS['ETH']
            token_debts[token] = round(debt, 4)
        data.append(
            {
                'Protocol': protocol,
                'ETH debt': token_debts['ETH'],
                'wBTC debt': token_debts['wBTC'],
                'USDC debt': token_debts['USDC'],
                'DAI debt': token_debts['DAI'],
                'USDT debt': token_debts['USDT'],
                'wstETH debt': token_debts['wstETH'],
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        data.to_csv("data/debt_stats.csv", index=False, compression='gzip')
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
            'wBTC utilization': debt_stats['wBTC debt'] / (supply_stats['wBTC supply'] + debt_stats['wBTC debt']),
            'USDC utilization': debt_stats['USDC debt'] / (supply_stats['USDC supply'] + debt_stats['USDC debt']),
            'DAI utilization': debt_stats['DAI debt'] / (supply_stats['DAI supply'] + debt_stats['DAI debt']),
            'USDT utilization': debt_stats['USDT debt'] / (supply_stats['USDT supply'] + debt_stats['USDT debt']),
            # TODO: hotfix to avoid `InvalidOperation: [<class 'decimal.DivisionUndefined'>]`
            'wstETH utilization': debt_stats['wstETH debt'].astype(float) / (
                supply_stats['wstETH supply'].astype(float) + debt_stats['wstETH debt'].astype(float)
            ),
        },
    )
    utilization_columns = [x for x in data.columns if 'utilization' in x]
    data[utilization_columns] = data[utilization_columns].applymap(lambda x: round(x, 4))
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        data.to_csv("data/utilization_stats.csv", index=False, compression='gzip')
    return data