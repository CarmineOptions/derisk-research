"""
This module defines the Dashboard class for rendering a DeRisk dashboard using Streamlit.
"""

import numpy as np
import pandas as pd
import plotly
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from data_handler.handlers.loan_states.abstractions import State
from shared.helpers import (
    add_leading_zeros,
    extract_token_addresses,
    fetch_token_symbols_from_set_of_loan_addresses,
    update_loan_data_with_symbols,
)

from helpers.settings import (
    COLLATERAL_TOKENS,
    DEBT_TOKENS,
    STABLECOIN_BUNDLE_NAME,
    TOKEN_SETTINGS,
)



from .constants import ChartsHeaders, CommonValues
from .main_chart_figure import (
    get_bar_chart_figures,
    get_main_chart_figure,
    get_specific_loan_usd_amounts,
    get_user_history,
    get_total_amount_by_field
)
from .utils import (
    get_protocol_data_mappings,
    infer_protocol_name,
    process_liquidity,
    transform_loans_data,
    transform_main_chart_data,
)
 


class Dashboard:
    """
    A class representing a dashboard for managing protocol names.
    """

    FIGURE_COLORS_DATA_MAPPING = {
        "collateral": plotly.express.colors.sequential.Oranges_r,
        "debt": plotly.express.colors.sequential.Greens_r,
        "supply": plotly.express.colors.sequential.Blues_r,
    }
    PROTOCOL_NAMES = [
        "zkLend",
        # "Nostra Alpha",
        # "Nostra Mainnet",
    ]

    def __init__(
            self,
            state: State | None = None,
            general_stats: dict | None = None,
            supply_stats: dict | None = None,
            collateral_stats: dict | None = None,
            debt_stats: dict | None = None,
            utilization_stats: dict | None = None,
    ):
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
        self.general_stats = pd.DataFrame(general_stats)
        self.supply_stats = pd.DataFrame(supply_stats)
        self.collateral_stats = pd.DataFrame(collateral_stats)
        self.debt_stats = pd.DataFrame(debt_stats)
        self.utilization_stats = pd.DataFrame(utilization_stats)

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
        ) = self._get_protocol_data_mappings()
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
        ) = self._get_protocol_data_mappings()
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
                max_value=int(loans_data[CommonValues.debt_usd.value].max()),
                value=(
                    0,
                    int(loans_data[CommonValues.debt_usd.value].max()) or 1,
                ),  # FIXME remove 1
            )

        st.dataframe(
            loans_data[
                (
                        loans_data[CommonValues.health_factor.value] > 0
                )  # TODO: debug the negative HFs
                & loans_data[CommonValues.debt_usd.value].between(
                    debt_usd_lower_bound, debt_usd_upper_bound
                )
                ]
            .sort_values(CommonValues.health_factor.value)
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
        ) = self._get_protocol_data_mappings()
        loans_data = transform_loans_data(
            protocol_loans_data_mapping, self.PROTOCOL_NAMES
        )

        st.header(ChartsHeaders.top_loans)
        col1, col2 = st.columns(2)
        loans_data[CommonValues.standardized_health_factor.value] = pd.to_numeric(
            loans_data[CommonValues.standardized_health_factor.value], errors="coerce"
        )
        with col1:
            st.subheader("Sorted by collateral")
            st.dataframe(
                loans_data[
                    (
                            loans_data[CommonValues.health_factor.value] > 1
                    )  # TODO: debug the negative HFs
                    & (
                            loans_data[CommonValues.standardized_health_factor.value]
                            != float("inf")
                    )
                    ]
                .sort_values(CommonValues.collateral_usd.value, ascending=False)
                .iloc[:20],
                use_container_width=True,
                )
        with col2:
            st.subheader("Sorted by debt")
            st.dataframe(
                loans_data[
                    (loans_data[CommonValues.health_factor.value] > 1)
                    & (
                            loans_data[CommonValues.standardized_health_factor.value]
                            != float("inf")
                    )  # TODO: debug the negative HFs
                    ]
                .sort_values(CommonValues.debt_usd.value, ascending=False)
                .iloc[:20],
                use_container_width=True,
                )

    def display_box(self):
        """
        Displays a box plot for collateral, debt, and deposit amounts.

        This method retrieves total amounts for collateral, debt, and deposit 
        from the class's data attributes, then visualizes them using a box plot.

        The box plot uses:
        - Green for Collateral
        - Red for Debt
        - Red for Deposit

        The plot is displayed using Streamlit.
        """
        collateral_df = get_total_amount_by_field(self.collateral_stats, 'collateral')
        debt_df = get_total_amount_by_field(self.debt_stats, 'debt')
        deposit_df = get_total_amount_by_field(self.supply_stats, 'deposit')
        
        boxplot_data = pd.DataFrame({
            "Collateral": collateral_df["total_amount"],
            "Debt": debt_df["total_amount"],
            "Deposit": deposit_df["total_amount"]
        })
        
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=boxplot_data, palette={"Collateral": "green", "Debt": "red", "Deposit": "red"})

        ax.set_ylabel("Total Amount")
        ax.set_title("Box Plot of Collateral, Debt, and Deposit")

        st.pyplot(fig)

    def load_detail_loan_chart(self):
        """
        Gererate a chart that shows detail loans.
        """
        (
            protocol_main_chart_data_mapping,
            protocol_loans_data_mapping,
        ) = self._get_protocol_data_mappings()
        loans_data = transform_loans_data(
            protocol_loans_data_mapping, self.PROTOCOL_NAMES
        )
        loans_data_main = loans_data.copy()

        token_symbols = None
        if not loans_data.empty:
            token_addresses = extract_token_addresses(loans_data)
            if token_addresses:
                token_symbols = fetch_token_symbols_from_set_of_loan_addresses(
                    token_addresses
                )
                loans_data = update_loan_data_with_symbols(loans_data, token_symbols)

        st.header(ChartsHeaders.detail_loans)
        col1, col2, col3 = st.columns(3)
        with col1:
            user = st.text_input(CommonValues.user.value)
            protocol = st.text_input(CommonValues.protocol.value)

            users_and_protocols_with_debt = list(
                loans_data.loc[
                    loans_data[CommonValues.debt_usd.value] > 0,
                    [CommonValues.user.value, CommonValues.protocol.value],
                ].itertuples(index=False, name=None)
            )
            random_user, random_protocol = users_and_protocols_with_debt[
                np.random.randint(len(users_and_protocols_with_debt))
            ]

            if not user:
                st.write(f"Selected random user = {random_user}.")
                user = random_user
            if not protocol:
                st.write(f"Selected random protocol = {random_protocol}.")
                protocol = random_protocol

            # Normalize the user address by adding leading zeroes if necessary
            user = add_leading_zeros(user)

            # Infer the correct protocol name using fuzzy matching
            valid_protocols = loans_data[CommonValues.protocol.value].unique()
            protocol = infer_protocol_name(protocol, valid_protocols)

        loan = loans_data_main.loc[
            (loans_data[CommonValues.user.value] == user)
            & (loans_data[CommonValues.protocol.value] == protocol),
        ]

        if loan.empty:
            st.warning(f"No loan found for user = {user} and protocol = {protocol}.")
        else:
            (
                collateral_usd_amounts,
                debt_usd_amounts,
            ) = get_specific_loan_usd_amounts(loan=loan)

            with col2:
                figure = plotly.express.pie(
                    collateral_usd_amounts,
                    values=CommonValues.amount_usd.value,
                    names=CommonValues.token.value,
                    title=CommonValues.collateral_usd.value,
                    color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
                )
                st.plotly_chart(figure, True)

            with col3:
                figure = plotly.express.pie(
                    debt_usd_amounts,
                    values=CommonValues.amount_usd.value,
                    names=CommonValues.token.value,
                    title=CommonValues.debt_usd.value,
                    color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
                )
                st.plotly_chart(figure, True)
            if token_symbols:
                st.dataframe(update_loan_data_with_symbols(loan, token_symbols))
            else:
                st.warning("No tokens found for curend user.")

    def load_comparison_lending_protocols_chart(self):
        """
        Gererate a chart that shows comparison lending protocols.
        """
        st.header(ChartsHeaders.comparison_lending_protocols)
        # Display dataframes
        st.dataframe(self.general_stats)
        st.dataframe(self.utilization_stats)
        # USD deposit, collateral and debt per token (bar chart).
        (
            supply_figure,
            collateral_figure,
            debt_figure,
        ) = get_bar_chart_figures(
            supply_stats=self.supply_stats.copy(),
            collateral_stats=self.collateral_stats.copy(),
            debt_stats=self.debt_stats.copy(),
        )
        st.plotly_chart(figure_or_data=supply_figure, use_container_width=True)
        st.plotly_chart(figure_or_data=collateral_figure, use_container_width=True)
        st.plotly_chart(figure_or_data=debt_figure, use_container_width=True)

        columns = st.columns(4)
        tokens = list(TOKEN_SETTINGS.keys())
        for column, token_1, token_2 in zip(columns, tokens[:4], tokens[4:]):
            with column:
                for token in [token_1, token_2]:
                    token = "wBTC" if token == "WBTC" else token
                    figure = self._plot_chart(token, "collateral")
                    st.plotly_chart(figure, True)

                for token in [token_1, token_2]:
                    figure = self._plot_chart(token, "debt")
                    st.plotly_chart(figure, True)

                for token in [token_1, token_2]:
                    if "dai" in token.lower():
                        continue
                    figure = self._plot_chart(token, "supply")
                    st.plotly_chart(figure, True)

    def get_user_history(self, wallet_id):  
        """  
        Fetch and return the transaction history for a specific user.  
        """  
        user_data = get_user_history(wallet_id)  
        if user_data is None or user_data.empty:  
            st.error("No data found for this user.")  
            return None  

        user_data.columns = [CommonValues.protocol.value, CommonValues.total_usd.value]  
        user_data = user_data.sort_values(CommonValues.total_usd.value, ascending=False)  
        user_data.reset_index(drop=True, inplace=True)  
        
        st.dataframe(user_data)  
        return user_data  

        # TODO: add last update functionality
        
    def load_leaderboard(self):
        """
        Display a leaderboard of the top 5 biggest collateral and debt per token.
        """
        st.header("Leaderboard: Top 5 Collateral & Debt per Token")
        
        if self.collateral_stats.empty or self.debt_stats.empty:
            st.warning("No data available for leaderboard.")
            return
        
        top_collateral = (
            self.collateral_stats.groupby("token")["amount_usd"]
            .sum()
            .nlargest(5)
            .reset_index()
        )
        top_collateral["type"] = "Collateral"
        
        top_debt = (
            self.debt_stats.groupby("token")["amount_usd"]
            .sum()
            .nlargest(5)
            .reset_index()
        )
        top_debt["type"] = "Debt"
        
        leaderboard_df = pd.concat([top_collateral, top_debt])
        
        def highlight_values(row):
            color = "green" if row["type"] == "Collateral" else "red"
            return [f'background-color: {color}; color: white' for _ in row]
        
        st.dataframe(
            leaderboard_df.style.apply(highlight_values, axis=1),
            hide_index=True,
            use_container_width=True,
        )

    def _plot_chart(self, token: str, stats_type: str) -> plotly.express.data:
        """
        Returns a ploted figure.
        :return plotly.express.Data: Figure.
        """
        return plotly.express.pie(
            getattr(self, f"{stats_type}_stats").reset_index(),
            values=f"{token} {stats_type}"
            if stats_type == "collateral"
            else f"{token} {stats_type}".lower(),
            names=CommonValues.protocol.value
            if stats_type == "collateral"
            else CommonValues.protocol.value.lower(),
            title=f"{token} {stats_type}",
            color_discrete_sequence=self.FIGURE_COLORS_DATA_MAPPING[stats_type],
        )

    def _get_protocol_data_mappings(self) -> tuple:
        """
        Return a tuple of protocol_main_chart_data_mapping and protocol_loans_data_mapping.
        :return: tuple
        """
        return get_protocol_data_mappings(
            current_pair=self.current_pair,
            stable_coin_pair=self.stable_coin_pair,
            protocols=self.PROTOCOL_NAMES,
            state=self.state,
        )

    def run(self):
        """
        This function executes/runs all chart loading methods.
        """
        # Load sidebar with protocol settings
        self.load_sidebar()
        self.load_main_chart()
        self.load_loans_with_low_health_factor_chart()
        self.load_top_loans_chart()
        self.load_detail_loan_chart()
        self.load_comparison_lending_protocols_chart()
        self.get_user_history()
        self.load_leaderboard()
