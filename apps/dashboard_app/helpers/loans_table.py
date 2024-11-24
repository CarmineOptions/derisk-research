import pandas as pd
from data_handler.handlers.loan_states.nostra_alpha.events import NostraAlphaState
from data_handler.handlers.loan_states.nostra_mainnet.events import NostraMainnetState
from data_handler.handlers.loan_states.zklend.events import ZkLendState
from shared.state import State
from shared.types import Prices


def get_protocol(state: State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, ZkLendState):
        return "zkLend"
    if isinstance(state, NostraAlphaState) and not isinstance(
        state, NostraMainnetState
    ):
        return "Nostra Alpha"
    if isinstance(state, NostraMainnetState):
        return "Nostra Mainnet"
    raise ValueError


def get_loans_table_data(
    state: State,
    prices: Prices,
) -> pd.DataFrame:
    """
    Get the loans table data.
    :param state: ZkLendState | NostraAlphaState | NostraMainnetState
    :param prices: Prices
    :return: DataFrame
    """
    data = []
    for loan_entity_id, loan_entity in state.loan_entities.items():
        collateral_usd = loan_entity.compute_collateral_usd(
            risk_adjusted=False,
            collateral_token_parameters=state.token_parameters.collateral,
            collateral_interest_rate_model=state.interest_rate_models.collateral,
            prices=prices,
        )
        risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
            risk_adjusted=True,
            collateral_token_parameters=state.token_parameters.collateral,
            collateral_interest_rate_model=state.interest_rate_models.collateral,
            prices=prices,
        )
        debt_usd = loan_entity.compute_debt_usd(
            risk_adjusted=False,
            debt_token_parameters=state.token_parameters.debt,
            debt_interest_rate_model=state.interest_rate_models.debt,
            prices=prices,
        )
        if isinstance(state, NostraAlphaState) or isinstance(state, NostraMainnetState):
            risk_adjusted_debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=True,
                debt_token_parameters=state.token_parameters.debt,
                debt_interest_rate_model=state.interest_rate_models.debt,
                prices=prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
            standardized_health_factor = loan_entity.compute_health_factor(
                standardized=True,
                collateral_token_parameters=state.token_parameters.collateral,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
        else:
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
            standardized_health_factor = loan_entity.compute_health_factor(
                standardized=True,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )

        data.append(
            {
                "User": loan_entity_id,
                "Protocol": get_protocol(state=state),
                "Collateral (USD)": collateral_usd,
                "Risk-adjusted collateral (USD)": risk_adjusted_collateral_usd,
                "Debt (USD)": debt_usd,
                "Health factor": health_factor,
                "Standardized health factor": standardized_health_factor,
                "Collateral": loan_entity.get_collateral_str(
                    collateral_token_parameters=state.token_parameters.collateral,
                    collateral_interest_rate_model=state.interest_rate_models.collateral,
                ),
                "Debt": loan_entity.get_debt_str(
                    debt_token_parameters=state.token_parameters.debt,
                    debt_interest_rate_model=state.interest_rate_models.debt,
                ),
            }
        )
    return pd.DataFrame(data)


def get_supply_function_call_parameters(
    protocol: str,
    token_addresses: list[str],
) -> tuple[list[str], str]:
    if protocol == "zkLend":
        return token_addresses, "felt_total_supply"
    if protocol in {"Nostra Alpha", "Nostra Mainnet"}:
        return token_addresses, "totalSupply"
    raise ValueError
