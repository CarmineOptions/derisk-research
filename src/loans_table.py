import pandas

import src.hashstack_v0
import src.helpers
import src.nostra_alpha
import src.nostra_mainnet
import src.protocol_parameters
import src.state



def get_loans_table_data(
    state: src.state.State,
    prices: src.helpers.TokenValues,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = []
    for loan_entity_id, loan_entity in state.loan_entities.items():
        collateral_usd = loan_entity.compute_collateral_usd(
            risk_adjusted=False,
            collateral_interest_rate_models=state.collateral_interest_rate_models,
            prices=prices,
        )
        risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
            risk_adjusted=True,
            collateral_interest_rate_models=state.collateral_interest_rate_models,
            prices=prices,
        )
        debt_usd = loan_entity.compute_debt_usd(
            risk_adjusted=False,
            debt_interest_rate_models=state.debt_interest_rate_models,
            prices=prices,
        )
        if (
            isinstance(state, src.nostra_alpha.NostraAlphaState)
            or isinstance(state, src.nostra_mainnet.NostraMainnetState)
        ):
            risk_adjusted_debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=True,
                debt_interest_rate_models=state.debt_interest_rate_models,
                prices=prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
            standardized_health_factor = loan_entity.compute_health_factor(
                standardized=True,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
        elif isinstance(state, src.hashstack_v0.HashstackV0State):
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                collateral_usd=collateral_usd,
                debt_usd=debt_usd,
            )
            standardized_health_factor = loan_entity.compute_health_factor(
                standardized=True,
                collateral_usd=collateral_usd,
                debt_usd=debt_usd,
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
                "User": (
                    loan_entity_id if not isinstance(state, src.hashstack_v0.HashstackV0State) else loan_entity.user
                ),
                "Protocol": src.protocol_parameters.get_protocol(state=state),
                "Collateral (USD)": collateral_usd,
                "Risk-adjusted collateral (USD)": risk_adjusted_collateral_usd,
                "Debt (USD)": debt_usd,
                "Health factor": health_factor,
                "Standardized health factor": standardized_health_factor,
                "Collateral": loan_entity.get_collateral_str(
                    collateral_interest_rate_models = state.collateral_interest_rate_models,
                ),
                "Debt": loan_entity.get_debt_str(debt_interest_rate_models = state.debt_interest_rate_models),
            }
        )
    data = pandas.DataFrame(data)
    if save_data:
        directory = src.protocol_parameters.get_directory(state=state)
        path = f"{directory}/loans.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data







