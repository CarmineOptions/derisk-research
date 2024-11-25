import streamlit as st

from dashboard_app.charts.main_chart_figure import get_main_chart_figure
from dashboard_app.charts.utils import process_liquidity
from dashboard_app.helpers.settings import (
    COLLATERAL_TOKENS,
    DEBT_TOKENS,
    STABLECOIN_BUNDLE_NAME,
)

from .utils import (
    get_protocol_data_mappings,
    transform_loans_data,
    transform_main_chart_data,
)


class Dashboard:
    PROTOCOL_NAMES = [
        "zkLend",
        # "Nostra Alpha",
        # "Nostra Mainnet",
    ]

    def __init__(self, zklend_state):
        """
        Initialize the dashboard.
        :param zklend_state: ZkLendState
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

    def load_sidebar(self):
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
        (
            protocol_main_chart_data_mapping,
            protocol_loans_data_mapping,
        ) = get_protocol_data_mappings(
            current_pair=self.current_pair,
            stable_coin_pair=self.stable_coin_pair,
            protocols=self.PROTOCOL_NAMES,
        )
        loans_data = transform_loans_data(
            protocol_loans_data_mapping, self.PROTOCOL_NAMES
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

    def run(self):
        # Load sidebar with protocol settings
        self.load_sidebar()
        self.load_main_chart()
