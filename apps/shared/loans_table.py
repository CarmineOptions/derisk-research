import pandas

from shared.types import Prices
from shared.state import State

from shared.helpers import get_protocol, get_directory


def get_loans_table_data(
    state: State,
    prices: Prices,
    save_data: bool = False,
) -> pandas.DataFrame:
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
                "User": (
                    loan_entity_id
                ),
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
    data = pandas.DataFrame(data)
    if save_data:
        directory = get_directory(state=state)
        path = f"{directory}/loans.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data