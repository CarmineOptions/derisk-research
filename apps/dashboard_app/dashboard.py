from __future__ import annotations

import logging
import streamlit as st
from py_scaffold.options import Option

from apps.dashboard_app.config import (
    ONE_MINUTE_IN_MILISECONDS,
    CRONTAB_TIME,
)
from apps.dashboard_app.state import state
from apps.dashboard_app.helpers.tools import (
    format_token_amount,
    format_usd_value,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REFRESH_TIME = ONE_MINUTE_IN_MILISECONDS * int(CRONTAB_TIME) * 10


def main() -> None:
    st.set_page_config(page_title="Derisk Research", page_icon="🔬", layout="wide")
    st.title("Derisk Research Dashboard")

    # Load data from Redis
    liquidable_data = state.get_liquidable_debt_from_redis()
    collateral_price = state.get_collateral_price_from_redis()
    debt_price = state.get_debt_price_from_redis()

    # Sidebar
    with st.sidebar:
        st.header("Token Prices")
        st.metric("Collateral Price", f"${collateral_price:.6f}")
        st.metric("Debt Price", f"${debt_price:.6f}")
        st.markdown(f"Auto-refresh: every {REFRESH_TIME // 1000} seconds")

    # Main content
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Liquidable Positions")
        if liquidable_data:
            liquidable = [d for d in liquidable_data if d.get("is_liquidable")]
            if liquidable:
                for pos in liquidable:
                    with st.expander(f"User: {pos['user'][:10]}..."):
                        st.write(f"**Collateral:** {format_token_amount(pos['collateral'])}")
                        st.write(f"**Debt:** {format_token_amount(pos['debt'])}")
                        st.write(f"**Liquidation Price:** ${pos['liquidation_price']}")
                        st.write(f"**Collateral Price:** ${pos['collateral_token_price']}")
            else:
                st.info("No liquidable positions found.")
        else:
            st.warning("No data available. Make sure data_handler is running.")

    with col2:
        st.subheader("All Positions")
        if liquidable_data:
            for pos in liquidable_data:
                with st.expander(f"User: {pos['user'][:10]}..."):
                    status = "🔴 Liquidable" if pos.get("is_liquidable") else "🟢 Safe"
                    st.write(f"**Status:** {status}")
                    st.write(f"**Collateral:** {format_token_amount(pos['collateral'])}")
                    st.write(f"**Debt:** {format_token_amount(pos['debt'])}")
                    st.write(f"**Liquidation Price:** ${pos['liquidation_price']}")
        else:
            st.info("No data available. Make sure data_handler is running.")


if __name__ == "__main__":
    main()
