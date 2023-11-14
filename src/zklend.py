from typing import Dict, Optional
import decimal
import logging

import pandas

import src.constants
import src.helpers
import src.state



ADDRESS: str = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"

# Keys are values of the "key_name" column in the database, values are the respective method names.
EVENTS_METHODS_MAPPING: Dict[str, str] = {
    "AccumulatorsSync": "process_accumulators_sync_event",
    "zklend::market::Market::AccumulatorsSync": "process_accumulators_sync_event",
    "Deposit": "process_deposit_event",
    "zklend::market::Market::Deposit": "process_deposit_event",
    "CollateralEnabled": "process_collateral_enabled_event",
    "zklend::market::Market::CollateralEnabled": "process_collateral_enabled_event",
    "CollateralDisabled": "process_collateral_disabled_event",
    "zklend::market::Market::CollateralDisabled": "process_collateral_disabled_event",
    "Withdrawal": "process_withdrawal_event",
    "zklend::market::Market::Withdrawal": "process_withdrawal_event",
    "Borrowing": "process_borrowing_event",
    "zklend::market::Market::Borrowing": "process_borrowing_event",
    "Repayment": "process_repayment_event",
    "zklend::market::Market::Repayment": "process_repayment_event",
    "Liquidation": "process_liquidation_event",
    "zklend::market::Market::Liquidation": "process_liquidation_event",
}

# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
COLLATERAL_FACTORS: Dict[str, decimal.Decimal] = {
    "ETH": decimal.Decimal("0.80"),
    "wBTC": decimal.Decimal("0.70"),
    "USDC": decimal.Decimal("0.80"),
    "DAI": decimal.Decimal("0.70"),
    "USDT": decimal.Decimal("0.70"),
    "wstETH": decimal.Decimal("0.80"),
}
# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
LIQUIDATION_BONUSES: Dict[str, decimal.Decimal] = {
    "ETH": decimal.Decimal("0.10"),
    "wBTC": decimal.Decimal("0.15"),
    "USDC": decimal.Decimal("0.10"),
    "DAI": decimal.Decimal("0.10"),
    "USDT": decimal.Decimal("0.10"),
    "wstETH": decimal.Decimal("0.10"),
}

SUPPLY_ADRESSES: Dict[str, str] = {
    "ETH": "0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1",
    "wBTC": "0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a",
    "USDC": "0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486",
    "DAI": "0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376",
    "USDT": "0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a",
    "wstETH": "0x0536aa7e01ecc0235ca3e29da7b5ad5b12cb881e29034d87a4290edbb20b7c28",
}



def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    return src.helpers.get_events(
        adresses = (ADDRESS, ''),
        events = tuple(EVENTS_METHODS_MAPPING),
        start_block_number = start_block_number,
    )


# TODO: Make this a dataclass?
class Accumulators:
    """
    A class that describes the state of the lending and debt accumulators which help transform face amounts into raw 
    amounts. Raw amount is the amount that would have been accumulated into the face amount if it were deposited at 
    genesis.
    """

    def __init__(self) -> None:
        self.lending_accumulator: decimal.Decimal = decimal.Decimal("1")
        self.debt_accumulator: decimal.Decimal = decimal.Decimal("1")


class ZkLendLoanEntity(src.state.LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`, it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in collateral. This is because 
    under zkLend, collateral is the amount deposited that is specificaly flagged with `collateral_enabled` set to True 
    for the given token. To properly account for the changes in collateral, we must hold the information about the 
    given token's deposits being enabled as collateral or not and the amount of the deposits. We keep all balances in raw 
    amounts.
    """

    COLLATERAL_FACTORS = COLLATERAL_FACTORS
    LIQUIDATION_BONUSES = LIQUIDATION_BONUSES

    def __init__(self) -> None:
        super().__init__()
        self.deposit: src.state.TokenAmounts = src.state.TokenAmounts()
        self.collateral_enabled: Dict[str, bool] = {x: False for x in src.constants.TOKEN_DECIMAL_FACTORS}


class ZkLendState(src.state.State):
    """
    A class that describes the state of all zkLend loan entities. It implements a method for correct processing of 
    every relevant event.
    """

    EVENTS_METHODS_MAPPING = EVENTS_METHODS_MAPPING

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=ZkLendLoanEntity,
            verbose_user=verbose_user,
        )
        self.accumulators: Dict[str, Accumulators] = {x: Accumulators() for x in src.constants.TOKEN_DECIMAL_FACTORS}

    def process_accumulators_sync_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `token`, `lending_accumulator`, `debt_accumulator`.
        # Example: https://starkscan.co/event/0x029628b89875a98c1c64ae206e7eb65669cb478a24449f3485f5e98aba6204dc_0.
        token = src.constants.get_symbol(event["data"][0])
        lending_accumulator = decimal.Decimal(str(int(event["data"][1], base=16))) / decimal.Decimal("1e27")
        debt_accumulator = decimal.Decimal(str(int(event["data"][2], base=16))) / decimal.Decimal("1e27")
        self.accumulators[token].lending_accumulator = lending_accumulator
        self.accumulators[token].debt_accumulator = debt_accumulator

    def process_deposit_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_3.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.accumulators[token].lending_accumulator
        self.loan_entities[user].deposit.increase_value(token=token, amount=raw_amount)
        if self.loan_entities[user].collateral_enabled[token]:
            self.loan_entities[user].collateral.increase_value(token=token, amount=raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was deposited.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_enabled_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_6.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        self.loan_entities[user].collateral_enabled[token] = True
        self.loan_entities[user].collateral.rewrite_value(
            token=token,
            amount=self.loan_entities[user].deposit.token_amounts[token],
        )
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, collateral was enabled for token = {}.'.format(
                    event["block_number"],
                    token,
                )
            )

    def process_collateral_disabled_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x0049b445bed84e0118795dbd22d76610ccac2ad626f8f04a1fc7e38113c2afe7_0.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        self.loan_entities[user].collateral_enabled[token] = False
        self.loan_entities[user].collateral.rewrite_value(token=token, amount=decimal.Decimal("0"))
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, collateral was disabled for token = {}.'.format(
                    event["block_number"],
                    token,
                )
            )

    def process_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x03472cf7511687a55bc7247f8765c4bbd2c18b70e09b2a10a77c61f567bfd2cb_4.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.accumulators[token].lending_accumulator
        self.loan_entities[user].deposit.increase_value(token=token, amount=-raw_amount)
        if self.loan_entities[user].collateral_enabled[token]:
            self.loan_entities[user].collateral.increase_value(token=token, amount=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was withdrawn.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_borrowing_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `raw_amount`, `face_amount`.
        # Example: https://starkscan.co/event/0x076b1615750528635cf0b63ca80986b185acbd20fa37f0f2b5368a4f743931f8_3.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        self.loan_entities[user].debt.increase_value(token=token, amount=raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was borrowed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_repayment_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `repayer`, `beneficiary`, `token`, `raw_amount`, 
        # `face_amount`.
        # Example: https://starkscan.co/event/0x06fa3dd6e12c9a66aeacd2eefa5a2ff2915dd1bb4207596de29bd0e8cdeeae66_5.
        user = event["data"][1]
        token = src.constants.get_symbol(event["data"][2])
        raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        self.loan_entities[user].debt.increase_value(token=token, amount=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was repayed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_liquidation_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `liquidator`, `user`, `debt_token`, `debt_raw_amount`, `debt_face_amount`,
        # `collateral_token`, `collateral_amount`.
        # Example: https://starkscan.co/event/0x07b8ec709df1066d9334d56b426c45440ca1f1bb841285a5d7b33f9d1008f256_5.
        user = event["data"][1]
        debt_token = src.constants.get_symbol(event["data"][2])
        debt_raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        collateral_token = src.constants.get_symbol(event["data"][5])
        collateral_face_amount = decimal.Decimal(str(int(event["data"][6], base=16)))
        collateral_raw_amount = (collateral_face_amount / self.accumulators[collateral_token].lending_accumulator)
        self.loan_entities[user].debt.increase_value(token=debt_token, amount=-debt_raw_amount)
        self.loan_entities[user].deposit.increase_value(token=collateral_token, amount=-collateral_raw_amount)
        if self.loan_entities[user].collateral_enabled[collateral_token]:
            self.loan_entities[user].collateral.increase_value(token=collateral_token, amount=-collateral_raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, debt of raw amount = {} of token = {} and collateral of raw amount = {} of '
                'token = {} were liquidated.'.format(
                    event["block_number"],
                    debt_raw_amount,
                    debt_token,
                    collateral_raw_amount,
                    collateral_token,
                )
            )