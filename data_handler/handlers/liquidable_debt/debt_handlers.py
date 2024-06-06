import pandas as pd
from decimal import Decimal

from handlers.state import State
from database.crud import DBConnector
from database.models import LiquidableDebt

from handlers.liquidable_debt.bases import Collector
from handlers.liquidable_debt.collectors import GoogleCloudDataCollector
from handlers.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                                             LOCAL_STORAGE_PATH, COLLATERAL_FIELD_NAME, PROTOCOL_FIELD_NAME,
                                             DEBT_FIELD_NAME, USER_FIELD_NAME, RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, DEBT_USD_FIELD_NAME, FIELDS_TO_VALIDATE,
                                             ALL_NEEDED_FIELDS, LIQUIDABLE_DEBT_FIELD_NAME, PRICE_FIELD_NAME,
                                             MYSWAP_VALUE, JEDISWAP_VALUE, POOL_SPLIT_VALUE)
from handlers.loan_states.zklend.events import ZkLendState
from handlers.helpers import TokenValues
from handlers.liquidable_debt.utils import Prices


class GCloudLiquidableDebtDataHandler:
    """
    A handler that collects data from Google Cloud Storage bucket,
    parses it and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :method: `update_data` -> Updates the data stored in the database.:
    """
    AVAILABLE_PROTOCOLS = [item.value for item in LendingProtocolNames]
    CONNECTOR = DBConnector()

    def __init__(
            self,
            loan_state_class: State,
            connection_url: str = GS_BUCKET_URL,
            bucket_name: str = GS_BUCKET_NAME,
            collector: Collector = GoogleCloudDataCollector
    ):
        self.collector = collector
        self.connection_url = connection_url
        self.bucket_name = bucket_name
        self.state_class = loan_state_class

    def prepare_data(self, protocol_name: str, path: str = LOCAL_STORAGE_PATH) -> dict:
        uploaded_file_path = self.collector.collect_data(
            protocol_name=protocol_name,
            available_protocols=self.AVAILABLE_PROTOCOLS,
            bucket_name=self.bucket_name,
            path=path,
            url=self.connection_url
        )
        parsed_data = self._parse_file(uploaded_file_path)  # till this line all is done

        return self._calculate_liquidable_debt(parsed_data)

    def _calculate_liquidable_debt(self, data: dict[int, dict[str, str | Decimal | dict[str, Decimal]]] = None):
        """
        Calculates liquidable debt based on data provided and updates an existing data.
        Data to calculate liquidable debt for:
        Args: data( dict[
            int - Row number,
            dict[
                str - Field name,
                str - Token value
                | Decimal - Field value (the price as example)
                | dict[
                    str - Token name,
                    Decimal - Token value
                ]
            ]
        ])
        :return: A dictionary of the ready liquidable debt data.
        """
        result_data = dict()
        prices = Prices()
        prices.get_lp_token_prices()

        for row_number, row_value in data.items():
            state = self.state_class(verbose_user=row_value[USER_FIELD_NAME])

            state.loan_entities[row_value[USER_FIELD_NAME]].debt.values = {
                key: value
                for key, value in row_value[DEBT_FIELD_NAME].items()
            }
            state.loan_entities[row_value[USER_FIELD_NAME]].collateral.values = {
                key: value
                for key, value in row_value[COLLATERAL_FIELD_NAME].items()
            }

            for token in row_value[DEBT_FIELD_NAME]:
                if not row_value[COLLATERAL_FIELD_NAME].get(token, ""):
                    continue

                result = state.compute_liquidable_debt_at_price(
                    prices=TokenValues(values=prices.prices.values),
                    collateral_token=token,
                    collateral_token_price=row_value[COLLATERAL_FIELD_NAME][token],
                    debt_token=token,
                    risk_adjusted_collateral_usd=row_value[RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME],
                    debt_usd=row_value[DEBT_USD_FIELD_NAME],
                    health_factor=row_value[HEALTH_FACTOR_FIELD_NAME],
                )

                if result > Decimal("0"):
                    result_data.update({
                        row_number: {
                            LIQUIDABLE_DEBT_FIELD_NAME: result,
                            PRICE_FIELD_NAME: prices.prices.values[token],
                            COLLATERAL_FIELD_NAME: token,
                            DEBT_FIELD_NAME: token,
                            PROTOCOL_FIELD_NAME: row_value[PROTOCOL_FIELD_NAME]
                        }
                    })

        return result_data

    @classmethod
    def _parse_file(cls, path: str = None) -> dict:
        """
        Parse a parquet file into a dictionary.
        :param path: The path to the parquet file.
        :return: A dictionary of the parsed data.
        """
        data = pd.read_parquet(path=path).to_dict()
        arranged_data = cls._arrange_data_by_row(data)

        for row_number in arranged_data:
            arranged_data[row_number][DEBT_FIELD_NAME] = cls._transform_str_into_dict(
                arranged_data[row_number][DEBT_FIELD_NAME]
            )
            arranged_data[row_number][COLLATERAL_FIELD_NAME] = cls._transform_str_into_dict(
                arranged_data[row_number][COLLATERAL_FIELD_NAME]
            )

        return arranged_data

    @classmethod
    def _arrange_data_by_row(cls, data: dict = None) -> dict:
        """
        Arranges the dictionary data by rows.
        :param data: The dictionary to arrange.
        :return: A dictionary of the arranged data.
        """
        result = dict()

        for row_number in data[DEBT_FIELD_NAME]:
            arranged_row = {
                USER_FIELD_NAME: data[USER_FIELD_NAME][row_number],
                PROTOCOL_FIELD_NAME: data[PROTOCOL_FIELD_NAME][row_number],
                RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME: data[RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME][row_number],
                DEBT_USD_FIELD_NAME: data[DEBT_USD_FIELD_NAME][row_number],
                HEALTH_FACTOR_FIELD_NAME: data[HEALTH_FACTOR_FIELD_NAME][row_number],
                COLLATERAL_FIELD_NAME: data[COLLATERAL_FIELD_NAME][row_number],
                DEBT_FIELD_NAME: data[DEBT_FIELD_NAME][row_number],
            }
            if cls._is_valid(arranged_row):
                result.update({row_number: arranged_row})

        return result

    @staticmethod
    def _is_valid(data: dict = None) -> bool:
        """
        Checks if the dictionary data is valid.
        :param data: The dictionary to check.
        :return: True if the dictionary data is valid, False otherwise.
        """
        for field in FIELDS_TO_VALIDATE:
            if not data[field]:
                return False

            if not isinstance(data[field], str):
                if data[field] <= Decimal("0") \
                        or data[field] == Decimal("inf"):
                    return False

        return True

    @classmethod
    def _transform_str_into_dict(cls, tokens: str) -> dict:
        """
        Transforms a string into a dictionary.
        :param tokens: The string to transform.
        :return: A dictionary of the transformed data.
        """
        result = dict()
        separeted_tokens = tokens.split(', ')

        for token in separeted_tokens:
            if not token:
                continue

            if MYSWAP_VALUE in token:
                current_token, value = cls.split_collateral(
                    token, f"{MYSWAP_VALUE}: "
                ).split(POOL_SPLIT_VALUE)
                result.update({current_token: Decimal(value)})

                continue

            if JEDISWAP_VALUE in token:
                current_token, value = cls.split_collateral(
                    token, f"{JEDISWAP_VALUE}: "
                ).split(POOL_SPLIT_VALUE)
                result.update({current_token: Decimal(value)})

                continue

            token, value = token.split(': ')
            result.update({token: Decimal(value)})

        return result

    @staticmethod
    def split_collateral(collateral_string: str, platform_name: str) -> list:
        """
        Removes a platform name from the collateral string.
        :param collateral_string: The collateral string to split.
        :param platform_name: The platform name.
        :return: A collateral string without the platform name.
        """
        result = collateral_string.split(platform_name)
        result.remove("")
        return next(iter(result))

    @classmethod
    def _write_to_db(cls, data: dict = None) -> None:
        """
        Writes the data into the database.
        :param data: A dictionary of the parsed data.
        :return: None
        """
        cls.CONNECTOR.write_to_db(LiquidableDebt(**data))


class DBLiquidableDebtDataHandler:
    # TODO write logic when it will be needed
    pass
