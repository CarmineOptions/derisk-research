import pandas
import math

import constants
import db
import streamlit as st


def get_events() -> pandas.DataFrame:
    latest_block = st.session_state.latest_block
    print("getting events from block", latest_block)
    # Establish the connection.
    connection = db.establish_connection()

    # Load all Zklend events.
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{constants.Protocol.ZKLEND.value}'
      AND
          key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
      AND
          block_number>{latest_block}
      ORDER BY
          block_number, id ASC;
      """,
        con=connection,
    )
    # Close the connection.
    connection.close()
    zklend_events.set_index("id", inplace=True)
    lb = zklend_events["block_number"].max()
    
    if not math.isnan(lb):
        print("new latest block", lb)
        st.session_state.latest_block = lb
    return zklend_events

def get_events() -> pandas.DataFrame:
    latest_block = st.session_state.latest_block
    print("getting events from block", latest_block)
    # Establish the connection.
    connection = db.establish_connection()

    # Load all Zklend events.
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{constants.Protocol.ZKLEND.value}'
      AND
          key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
      AND
          block_number>{latest_block}
      ORDER BY
          block_number, id ASC;
      """,
        con=connection,
    )
    # Close the connection.
    connection.close()
    zklend_events.set_index("id", inplace=True)
    lb = zklend_events["block_number"].max()
    
    if not math.isnan(lb):
        print("new latest block", lb)
        st.session_state.latest_block = lb
    return zklend_events

def get_events_hash(): 
    connection = db.establish_connection()
    hashstack_events = pandas.read_sql(
        sql = 
        f"""
        SELECT
            *
        FROM
            starkscan_events
        WHERE
            from_address='{constants.Protocol.HASHSTACK.value}'
        AND
            key_name IN ('new_loan', 'loan_withdrawal', 'loan_repaid', 'loan_swap', 'collateral_added', 'collateral_withdrawal', 'loan_interest_deducted', 'liquidated')
        ORDER BY
            block_number, id ASC;
        """,
        con = connection,
    )

    # Close the connection.
    connection.close()
    hashstack_events.set_index('id', inplace = True)
    hashstack_events['order'] = hashstack_events['key_name'].map(
        {
            'new_loan': 0,
            'loan_withdrawal': 3,
            'loan_repaid': 4,
            'loan_swap': 1,
            'collateral_added': 6,
            'collateral_withdrawal': 7,
            'loan_interest_deducted': 5,
            'liquidated': 2,
        },
    )
    hashstack_events.sort_values(['block_number', 'transaction_hash', 'order'], inplace = True)
    return hashstack_events
