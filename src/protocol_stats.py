import asyncio
import decimal
import os

import pandas

import src.blockchain_call
import src.hashstack
import src.helpers
import src.protocol_parameters
import src.settings
import src.state



def get_general_stats(
    states: list[src.state.State],
    loan_stats: dict[str, pandas.DataFrame],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
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
        # TODO: Save to parquet.
        path = "data/general_stats.csv"
        data.to_csv(path, index=False, compression='gzip')
        src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
        os.remove(path)
    return data


def get_supply_stats(
    states: list[src.state.State],
    prices: src.helpers.TokenValues,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_supplies = {}
        for token in src.settings.TOKEN_SETTINGS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_supplies[token] = decimal.Decimal("0")
                continue
            if protocol == 'Hashstack':
                supply = asyncio.run(
                    src.blockchain_call.balance_of(
                        token_addr = src.settings.TOKEN_SETTINGS[token].address,
                        holder_addr = src.hashstack.ADDRESS,
                    )
                )
            else:
                address, selector = src.protocol_parameters.get_supply_function_call_parameters(
                    protocol=protocol, 
                    token=token,
                )
                supply = asyncio.run(
                    src.blockchain_call.func_call(
                        addr = int(address, base=16),
                        selector = selector,
                        calldata = [],
                    )
                )[0]
            supply = decimal.Decimal(str(supply)) / src.settings.TOKEN_SETTINGS[token].decimal_factor
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
        data[column] * prices.values[column.split(' ')[0]] 
        for column in data.columns 
        if 'supply' in column
    ).apply(lambda x: round(x, 4))
    if save_data:
        # TODO: Save to parquet.
        path = "data/supply_stats.csv"
        data.to_csv(path, index=False, compression='gzip')
        src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
        os.remove(path)
    return data


def get_collateral_stats(
    states: list[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_collaterals = {}
        for token in src.settings.TOKEN_SETTINGS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_collaterals[token] = decimal.Decimal("0")
                continue
            collateral = (
                sum(
                    loan_entity.collateral.values[token]
                    for loan_entity in state.loan_entities.values()
                )
                / src.settings.TOKEN_SETTINGS[token].decimal_factor
                * state.collateral_interest_rate_models.values[token]
            )
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
        # TODO: Save to parquet.
        path = "data/collateral_stats.csv"
        data.to_csv(path, index=False, compression='gzip')
        src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
        os.remove(path)
    return data


def get_debt_stats(
    states: list[src.state.State],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        token_debts = {}
        for token in src.settings.TOKEN_SETTINGS:
            if token == 'wstETH' and protocol != 'zkLend':
                token_debts[token] = decimal.Decimal("0")
                continue
            debt = (
                sum(
                    loan_entity.debt.values[token]
                    for loan_entity in state.loan_entities.values()
                )
                / src.settings.TOKEN_SETTINGS[token].decimal_factor
                * state.debt_interest_rate_models.values[token]
            )
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
        # TODO: Save to parquet.
        path = "data/debt_stats.csv"
        data.to_csv(path, index=False, compression='gzip')
        src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
        os.remove(path)
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
        # TODO: Save to parquet.
        path = "data/utilization_stats.csv"
        data.to_csv(path, index=False, compression='gzip')
        src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
        os.remove(path)
    return data