"""
This module defines the Dashboard class for rendering a DeRisk dashboard using Streamlit.
"""
import pandas as pd
import streamlit as st
from data_handler.handlers.loan_states.abstractions import State
from shared.helpers import (
    extract_token_addresses,
    fetch_token_symbols_from_set_of_loan_addresses,
    update_loan_data_with_symbols,
)

from helpers.settings import COLLATERAL_TOKENS, DEBT_TOKENS, STABLECOIN_BUNDLE_NAME

from .constants import ChartsHeaders
from .main_chart_figure import get_main_chart_figure
from .utils import (
    get_protocol_data_mappings,
    process_liquidity,
    transform_loans_data,
    transform_main_chart_data,
)


class Dashboard:
    """
    A class representing a dashboard for managing protocol names.
    """

    PROTOCOL_NAMES = [
        "zkLend",
        # "Nostra Alpha",
        # "Nostra Mainnet",
    ]

    def __init__(self, state: State):
        """
        Initialize the dashboard.
        """
        # Set the page configuration
        st.set_page_config(
            layout="wide",
            page_title="DeRisk by Carmine Finance",
            page_icon="https://carmine.finance/assets/logo.svg",
        )
        # Setting up page title
        st.title("DeRisk")
        # Initializing variables
        self.collateral_token = None
        self.protocols = []
        self.debt_token = None
        self.current_pair = None
        self.stable_coin_pair = None
        self.collateral_token_price = 0
        self.state = state

    def load_sidebar(self):
        """
        Creates an interactive sidebar for selecting multiple protocols, debt and collateral token.
        """
        col1, _ = st.columns([1, 3])
        with col1:
            self.protocols = st.multiselect(
                label="Select protocols",
                options=self.PROTOCOL_NAMES,
                default=self.PROTOCOL_NAMES,
            )
            self.collateral_token = st.selectbox(
                label="Select collateral token:",
                options=COLLATERAL_TOKENS,
                index=0,
            )

            self.debt_token = st.selectbox(
                label="Select debt token:",
                options=DEBT_TOKENS,
                index=0,
            )

            # Updating pair details
            self.stable_coin_pair = f"{self.collateral_token}-{STABLECOIN_BUNDLE_NAME}"
            self.current_pair = f"{self.collateral_token}-{self.debt_token}"

            if self.debt_token == self.collateral_token:
                st.warning(
                    "⚠️ You are selecting the same token for both collateral and debt."
                )

    def load_main_chart(self):
        """
        Generates a chart that visualizes liquidable debt against available supply.
        """
        (
            protocol_main_chart_data_mapping,
            protocol_loans_data_mapping,
        ) = get_protocol_data_mappings(
            current_pair=self.current_pair,
            stable_coin_pair=self.stable_coin_pair,
            protocols=self.PROTOCOL_NAMES,
            state=self.state,
        )
        loans_data = (  # TODO: remove unused `loans_data` variable or use it
            transform_loans_data(protocol_loans_data_mapping, self.PROTOCOL_NAMES)
        )
        main_chart_data = transform_main_chart_data(
            protocol_main_chart_data_mapping, self.current_pair, self.PROTOCOL_NAMES
        )

        # Plot the liquidable debt against the available supply.
        collateral_token, debt_token = self.current_pair.split("-")
        collateral_token_price = 0

        if self.current_pair == self.stable_coin_pair:
            for stable_coin in DEBT_TOKENS[:-1]:
                debt_token = stable_coin
                main_chart_data, collateral_token_price = process_liquidity(
                    main_chart_data, collateral_token, debt_token
                )
        else:
            main_chart_data, collateral_token_price = process_liquidity(
                main_chart_data, collateral_token, debt_token
            )

        figure = get_main_chart_figure(
            data=main_chart_data,
            collateral_token=collateral_token,
            debt_token=(
                STABLECOIN_BUNDLE_NAME
                if self.current_pair == self.stable_coin_pair
                else debt_token
            ),
            collateral_token_price=collateral_token_price,
        )
        st.plotly_chart(figure_or_data=figure, use_container_width=True)

    def load_loans_with_low_health_factor_chart(self):
        """
        Gererate a chart that shows loans with low health factor.
        """
        (
            protocol_main_chart_data_mapping,
            protocol_loans_data_mapping,
        ) = get_protocol_data_mappings(
            current_pair=self.current_pair,
            stable_coin_pair=self.stable_coin_pair,
            protocols=self.PROTOCOL_NAMES,
            state=self.state,
        )
        loans_data = transform_loans_data(
            protocol_loans_data_mapping, self.PROTOCOL_NAMES
        )

        token_addresses = extract_token_addresses(loans_data)
        if token_addresses:
            token_symbols = fetch_token_symbols_from_set_of_loan_addresses(
                token_addresses
            )
            loans_data = update_loan_data_with_symbols(loans_data, token_symbols)

        st.header(ChartsHeaders.low_health_factor_loans)

        col1, _ = st.columns([1, 3])
        with col1:
            # TODO: remove this line when debugging is done
            debt_usd_lower_bound, debt_usd_upper_bound = st.slider(
                label="Select range of USD borrowings",
                min_value=0,
                max_value=int(loans_data["Debt (USD)"].max()),
                value=(0, int(loans_data["Debt (USD)"].max()) or 1),  # FIXME remove 1
            )

        st.dataframe(
            loans_data[
                (loans_data["Health factor"] > 0)  # TODO: debug the negative HFs
                & loans_data["Debt (USD)"].between(
                    debt_usd_lower_bound, debt_usd_upper_bound
                )
            ]
            .sort_values("Health factor")
            .iloc[:20],
            use_container_width=True,
        )

    def load_top_loans_chart(self):
        """
        Gererate a chart that shows top loans.
        """
        (
            protocol_main_chart_data_mapping,
            protocol_loans_data_mapping,
        ) = get_protocol_data_mappings(
            current_pair=self.current_pair,
            stable_coin_pair=self.stable_coin_pair,
            protocols=self.PROTOCOL_NAMES,
            state=self.state,
        )
        loans_data = transform_loans_data(
            protocol_loans_data_mapping, self.PROTOCOL_NAMES
        )

        st.header(ChartsHeaders.top_loans)
        col1, col2 = st.columns(2)
        loans_data["Standardized health factor"] = pd.to_numeric(
            loans_data["Standardized health factor"], errors="coerce"
        )
        with col1:
            st.subheader("Sorted by collateral")
            st.dataframe(
                loans_data[
                    (loans_data["Health factor"] > 1)  # TODO: debug the negative HFs
                    & (loans_data["Standardized health factor"] != float("inf"))
                ]
                .sort_values("Collateral (USD)", ascending=False)
                .iloc[:20],
                use_container_width=True,
            )
        with col2:
            st.subheader("Sorted by debt")
            st.dataframe(
                loans_data[
                    (loans_data["Health factor"] > 1)
                    & (
                        loans_data["Standardized health factor"] != float("inf")
                    )  # TODO: debug the negative HFs
                ]
                .sort_values("Debt (USD)", ascending=False)
                .iloc[:20],
                use_container_width=True,
            )

    def run(self):
        """
        This function executes/runs the load_sidebar() and load_main_chart() function.
        """
        # Load sidebar with protocol settings
        self.load_sidebar()
        self.load_main_chart()
        self.load_loans_with_low_health_factor_chart()
        self.load_top_loans_chart()
