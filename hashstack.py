import collections
import decimal

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


class HashStackBorrowings:
    """
    TODO
    """

    def __init__(
        self,
        borrowings_id: int,
        market: str,
        amount: decimal.Decimal,
        current_market: str,
        current_amount: decimal.Decimal,
        debt_category: int,
    ) -> None:
        self.id: int = borrowings_id
        self.market: str = market
        self.amount: decimal.Decimal = amount
        self.current_market: str = current_market
        self.current_amount: decimal.Decimal = current_amount
        self.debt_category: int = debt_category


class HashStackCollateral:
    """
    TODO
    """

    def __init__(
        self,
        market: str,
        amount: decimal.Decimal,
        current_amount: decimal.Decimal,
    ) -> None:
        self.market: str = market
        self.amount: decimal.Decimal = amount
        self.current_amount: decimal.Decimal = current_amount


class HashStackLoan:
    """
    TODO
    """

    def __init__(
        self,
        borrowings: HashStackBorrowings,
        collateral: HashStackCollateral,
    ) -> None:
        self.borrowings: HashStackBorrowings = borrowings
        self.collateral: HashStackCollateral = collateral


class UserState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.loans: Dict[int, HashStackLoan] = {}


class State:
    """
    TODO
    """

    # TODO: f'process_{name.lower()}_event'?
    EVENTS_FUNCTIONS_MAPPING: Dict[str, str] = {
        "new_loan": "process_new_loan_event",
        # TODO: this event shows what the user does with the loan, but it shouldn't change the amount borrowed, so let's ignore it for now
#         "loan_withdrawal": "process_loan_withdrawal_event",
        "loan_repaid": "process_loan_repaid_event",
        "loan_swap": "process_loan_swap_event",
        "collateral_added": "process_collateral_added_event",
        "collateral_withdrawal": "process_collateral_withdrawal_event",
        "loan_interest_deducted": "process_loan_interest_deducted_event",
        "liquidated": "process_liquidated_event",
    }

    def __init__(self) -> None:
        # TODO: how to compute the interest accrued on both collateral and loan?
        self.user_loan_ids_mapping: collections.defaultdict = collections.defaultdict(list)
        self.user_states: collections.defaultdict = collections.defaultdict(UserState)

    def process_event(self, event: pandas.Series) -> None:
        # TODO: filter events in the query
        if not event["key_name"] in self.EVENTS_FUNCTIONS_MAPPING:
            return
        getattr(self, self.EVENTS_FUNCTIONS_MAPPING[event["key_name"]])(event=event)

    def process_new_loan_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, 
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `market`, `amount`, `current_amount`, `commitment`, `timelock_validity`, `is_timelock_activated`,
        # `activation_time`, `timestamp`.
        loan_id = int(event["data"][0], base = 16)
        user = event["data"][1]
        self.user_loan_ids_mapping[user].append(loan_id)
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        borrowings_token = constants.get_symbol(event["data"][2])
        borrowings_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowings_current_token = constants.get_symbol(event["data"][6])
        borrowings_current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        debt_category = int(event["data"][10], base=16)
        # TODO: first ~3 loans seem to have different structure of 'data'
        try:
            collateral_token = constants.get_symbol(event["data"][14])
            collateral_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
            collateral_current_amount = decimal.Decimal(str(int(event["data"][17], base=16)))
        except KeyError:
            collateral_token = constants.get_symbol(event["data"][13])
            collateral_amount = decimal.Decimal(str(int(event["data"][14], base=16)))
            collateral_current_amount = decimal.Decimal(str(int(event["data"][16], base=16)))
        self.user_states[user].loans[loan_id] = HashStackLoan(
            borrowings = HashStackBorrowings(
                borrowings_id = loan_id,
                market = borrowings_token,
                amount = borrowings_amount,
                current_market = borrowings_current_token,
                current_amount = borrowings_current_amount,
                debt_category = debt_category,
            ),
            collateral = HashStackCollateral(
                market = collateral_token,
                amount = collateral_amount,
                current_amount = collateral_current_amount,
            ),
        )

    def process_loan_repaid_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, 
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `timestamp`.
        loan_id = int(event["data"][0], base = 16)
        user = event["data"][1]
        token = constants.get_symbol(event["data"][2])
        amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        current_token = constants.get_symbol(event["data"][6])
        current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        # TODO: from the docs it seems that it's only possible to repay the whole amount
        assert current_amount == decimal.Decimal('0')
        debt_category = int(event["data"][10], base=16)
        self.user_states[user].loans[loan_id].borrowings = HashStackBorrowings(
            borrowings_id = loan_id,
            market = token,
            amount = amount,
            current_market = current_token,
            current_amount = current_amount,
            debt_category = debt_category,
        )

    def process_loan_swap_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, 
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, `current_amount`,
        # `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`, `timestamp`.
        old_loan_id = int(event["data"][0], base = 16)
        old_user = event["data"][1]
        assert old_loan_id in self.user_loan_ids_mapping[old_user]
        new_loan_id = int(event["data"][14], base = 16)
        new_user = event["data"][15]
        assert old_loan_id == new_loan_id
        # TODO: this doesn't always have to hold, right?
        assert old_user == new_user
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        new_token = constants.get_symbol(event["data"][16])
        new_amount = decimal.Decimal(str(int(event["data"][18], base=16)))
        assert self.user_states[old_user].loans[old_loan_id].borrowings.market == new_token
        assert self.user_states[old_user].loans[old_loan_id].borrowings.amount == new_amount
        new_current_token = constants.get_symbol(event["data"][20])
        new_current_amount = decimal.Decimal(str(int(event["data"][21], base=16)))
        old_debt_category = int(event["data"][10], base=16)
        new_debt_category = int(event["data"][24], base=16)
        # TODO: this need to hold, right?
        assert old_debt_category == new_debt_category
        # TODO: from the docs it seems that it's only possible to swap the whole balance
        self.user_states[new_user].loans[new_loan_id].borrowings = HashStackBorrowings(
            borrowings_id = new_loan_id,
            market = new_token,
            amount = new_amount,
            current_market = new_current_token,
            current_amount = new_current_amount,
            debt_category = new_debt_category,
        )

    def process_collateral_added_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `loan_id`, `amount_added`,
        # `timestamp`.
        loan_id = int(event["data"][9], base = 16)
        # TODO: create method self.find_user?
        users = [user for user, loan_ids in self.user_loan_ids_mapping.items() if loan_id in loan_ids]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_added`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market = token,
            amount = amount,
            current_amount = current_amount,
        )

    def process_collateral_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `loan_id`, `amount_withdrawn`,
        # `timestamp`.
        loan_id = int(event["data"][9], base = 16)
        # TODO: create method self.find_user?
        users = [user for user, loan_ids in self.user_loan_ids_mapping.items() if loan_id in loan_ids]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_withdrawn`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market = token,
            amount = amount,
            current_amount = current_amount,
        )

    def process_loan_interest_deducted_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `accrued_interest`, `loan_id`,
        # `timestamp`.
        loan_id = int(event["data"][11], base = 16)
        # TODO: create method self.find_user?
        users = [user for user, loan_ids in self.user_loan_ids_mapping.items() if loan_id in loan_ids]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_withdrawn`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market = token,
            amount = amount,
            current_amount = current_amount,
        )

    def process_liquidated_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, 
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `liquidator`, `timestamp`.
        loan_id = int(event["data"][0], base = 16)
        user = event["data"][1]
        token = constants.get_symbol(event["data"][2])
        amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        current_token = constants.get_symbol(event["data"][6])
        current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        # TODO: from the docs it seems that it's only possible to liquidate the whole amount
        assert current_amount == decimal.Decimal('0')
        debt_category = int(event["data"][10], base=16)
        self.user_states[user].loans[loan_id].borrowings = HashStackBorrowings(
            borrowings_id = loan_id,
            market = token,
            amount = amount,
            current_market = current_token,
            current_amount = current_amount,
            debt_category = debt_category,
        )
        # TODO: what happens to the collateral? now assuming it disappears
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market = self.user_states[user].loans[loan_id].collateral.market,
            amount = self.user_states[user].loans[loan_id].collateral.amount,
            current_amount = decimal.Decimal('0'),
        )






























