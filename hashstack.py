import pandas

import src.db


def get_hashstack_events() -> pandas.DataFrame:
    connection = src.db.establish_connection()
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
    connection.close()
    hashstack_events.set_index("id", inplace=True)
    # TODO: ensure we're processing loan_repaid after all other loan-altering events + other events in "logical" order
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