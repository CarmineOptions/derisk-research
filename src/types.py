import abc
import collections
import dataclasses
import decimal



def _interest_rate_model_default() -> decimal.Decimal:
    return decimal.Decimal("1")


class InterestRateModels(collections.defaultdict):
    """
    A class that describes the state of the interest rate indices for multiple tokens. The indices help transform face 
    amounts into raw amounts. The raw amount is the amount that would have been accumulated into the face amount if it 
    were deposited at genesis.
    """

    def __init__(self) -> None:
        # TODO: this is a workaround, without it, the class can't be pickled. Remove after we don't store the results as pickles anymore
        super().__init__(_interest_rate_model_default)
        # super().__init__(lambda: decimal.Decimal("1"))


class CollateralAndDebtInterestRateModels:
    """
    A class that describes the state of the collateral and debt interest rate indices for multiple tokens. The indices 
    help transform face amounts into raw amounts. The raw amount is the amount that would have been accumulated into 
    the face amount if it were deposited at genesis.
    """

    def __init__(self) -> None:
        # These models reflect the interest rates at which users lend/stake funds.
        self.collateral: InterestRateModels = InterestRateModels()
        # These models reflect the interest rates at which users borrow funds.
        self.debt: InterestRateModels = InterestRateModels()


# TODO: Rounding errors?
# TODO: Relevant interest rate models?
@dataclasses.dataclass
class BaseTokenParameters:
    address: str
    decimals: int
    symbol: str
    underlying_symbol: str
    underlying_address: str


def _base_token_parameters_default() -> BaseTokenParameters:
    return BaseTokenParameters(
        address='',
        decimals=0,
        symbol='',
        underlying_symbol='',
        underlying_address='',
    )


class TokenParameters(collections.defaultdict):
    """
    A class that describes the parameters of collateral or debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self) -> None:
        # TODO: this is a workaround, without it, the class can't be pickled. Remove after we don't store the results as pickles anymore
        super().__init__(_base_token_parameters_default)
        # super().__init__(
        #     lambda: BaseTokenParameters(
        #         address='',
        #         decimals=0,
        #         symbol='',
        #         underlying_symbol='',
        #         underlying_address='',
        #     ),
        # )


class CollateralAndDebtTokenParameters:
    """
    A class that describes the parameters of collateral and debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self) -> None:
        self.collateral: TokenParameters = TokenParameters()  # TODO: add `collateral_factor``
        self.debt: TokenParameters = TokenParameters()  # TODO: add `debt_factor`


class Portfolio(collections.defaultdict):
    """A class that describes holdings of tokens."""

    # TODO: Update the values.
    MAX_ROUNDING_ERRORS: collections.defaultdict = collections.defaultdict(
        lambda: decimal.Decimal("5e12"),
        **{
            # Tokens allowed by zkLend.
            "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": decimal.Decimal("5e12"),  # ETH
            "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac": decimal.Decimal("1e2"),  # WBTC
            "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": decimal.Decimal("1e4"),  # USDC
            "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3": decimal.Decimal("1e16"),  # DAI
            "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8": decimal.Decimal("1e4"),  # USDT
            "0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2": decimal.Decimal("5e12"),  # wstETH
            "0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49": decimal.Decimal("5e12"),  # LORDS
            "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d": decimal.Decimal("5e12"),  # STRK
            # Tokens allowed by Nostra Alpha.
            '0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9': decimal.Decimal("1e2"),  # iWBTC-c
            '0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53': decimal.Decimal("1e2"),  # nWBTC-c
            '0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7': decimal.Decimal("1e2"),  # dWBTC
            '0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6': decimal.Decimal("5e12"),  # iETH-c
            '0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453': decimal.Decimal("5e12"),  # nETH-c
            '0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5': decimal.Decimal("5e12"),  # dETH
            '0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e': decimal.Decimal("1e4"),  # iUSDC-c
            '0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833': decimal.Decimal("1e4"),  # nUSDC-c
            '0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a': decimal.Decimal("1e4"),  # dUSDC
            '0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58': decimal.Decimal("1e16"),  # iDAI-c
            '0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17': decimal.Decimal("1e16"),  # nDAI-c
            '0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb': decimal.Decimal("1e16"),  # dDAI
            '0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0': decimal.Decimal("1e4"),  # iUSDT-c
            '0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601': decimal.Decimal("1e4"),  # nUSDT-c
            '0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6': decimal.Decimal("1e4"),  # dUSDT
            # Tokens allowed by Nostra Mainnet.
            '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c': decimal.Decimal("1e2"),  # iWBTC-c
            '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa': decimal.Decimal("1e2"),  # nWBTC-c
            '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': decimal.Decimal("1e2"),  # dWBTC
            '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8': decimal.Decimal("5e12"),  # iETH-c
            '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893': decimal.Decimal("5e12"),  # nETH-c
            '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': decimal.Decimal("5e12"),  # dETH
            '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6': decimal.Decimal("1e4"),  # iUSDC-c
            '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4': decimal.Decimal("1e4"),  # nUSDC-c
            '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': decimal.Decimal("1e4"),  # dUSDC
            '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9': decimal.Decimal("1e16"),  # iDAI-c
            '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70': decimal.Decimal("1e16"),  # nDAI-c
            '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': decimal.Decimal("1e16"),  # dDAI
            '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83': decimal.Decimal("1e4"),  # iUSDT-c
            '0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313': decimal.Decimal("1e4"),  # nUSDT-c
            '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': decimal.Decimal("1e4"),  # dUSDT
            '0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a': decimal.Decimal("5e12"),  # iwstETH-c
            '0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb': decimal.Decimal("5e12"),  # nwstETH-c
            '0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb': decimal.Decimal("5e12"),  # dwstETH
            '0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd': decimal.Decimal("1e16"),  # iLORDS-c
            '0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4': decimal.Decimal("1e16"),  # nLORDS-c
            '0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8': decimal.Decimal("1e16"),  # dLORDS
            '0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b': decimal.Decimal("5e12"),  # iSTRK-c
            '0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf': decimal.Decimal("5e12"),  # nSTRK-c
            '0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947': decimal.Decimal("5e12"),  # dSTRK
            '0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5': decimal.Decimal("5e12"),  # instSTRK-c
            '0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5': decimal.Decimal("5e12"),  # nnstSTRK-c
            '0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b': decimal.Decimal("5e12"),  # dnstSTRK
            '0x02a3a9d7bcecc6d3121e3b6180b73c7e8f4c5f81c35a90c8dd457a70a842b723': decimal.Decimal("5e12"),  # iUNO-c
            '0x07d717fb27c9856ea10068d864465a2a8f9f669f4f78013967de06149c09b9af': decimal.Decimal("5e12"),  # nUNO-c
            '0x04b036839a8769c04144cc47415c64b083a2b26e4a7daa53c07f6042a0d35792': decimal.Decimal("5e12"),  # dUNO
            '0x046ab56ec0c6a6d42384251c97e9331aa75eb693e05ed8823e2df4de5713e9a4': decimal.Decimal("5e12"),  # iNSTR-c
            '0x06f8ad459c712873993e9ffb9013a469248343c3d361e4d91a8cac6f98575834': decimal.Decimal("5e12"),  # nNSTR-c
            '0x03e0576565c1b51fcac3b402eb002447f21e97abb5da7011c0a2e0b465136814': decimal.Decimal("5e12"),  # dNSTR
            '0x06726ec97bae4e28efa8993a8e0853bd4bad0bd71de44c23a1cd651b026b00e7': decimal.Decimal("5e12"),  # dDAI V2
        },
    )

    def __init__(self, **kwargs) -> None:
        assert all(isinstance(x, str) for x in kwargs.keys())
        assert all(isinstance(x, decimal.Decimal) for x in kwargs.values())
        super().__init__(decimal.Decimal, **kwargs)

    def __add__(self, second_portfolio: 'Portfolio') -> 'Portfolio':
        if not isinstance(second_portfolio, Portfolio):
            raise TypeError(f"Cannot add {type(second_portfolio)} to Portfolio.")
        new_portfolio = Portfolio()
        for token, amount in self.items():
            new_portfolio[token] += amount
        for token, amount in second_portfolio.items():
            new_portfolio[token] += amount
        return new_portfolio

    # TODO: Find a better solution to fix the discrepancies.
    def round_small_value_to_zero(self, token: str):
        if abs(self[token]) < self.MAX_ROUNDING_ERRORS[token]:
            self[token] = decimal.Decimal("0")

    def increase_value(self, token: str, value: decimal.Decimal):
        self[token] += value
        self.round_small_value_to_zero(token=token)

    def set_value(self, token: str, value: decimal.Decimal):
        self[token] = value
        self.round_small_value_to_zero(token=token)


class Prices(collections.defaultdict):
    """ A class that describes the prices of tokens. """

    def __init__(self) -> None:
        super().__init__(lambda: None)


class LoanEntity(abc.ABC):
    """
    A class that describes and entity which can hold collateral, borrow debt and be liquidable. For example, on 
    Starknet, such an entity is the user in case of zkLend, Nostra Alpha and Nostra Mainnet, or an individual loan in 
    case od Hashstack V0 and Hashstack V1.
    """

    def __init__(self) -> None:
        self.collateral: Portfolio = Portfolio()
        self.debt: Portfolio = Portfolio()

    def compute_collateral_usd(
        self,
        risk_adjusted: bool,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
        prices: Prices,
    ) -> float:
        return sum(
            float(token_amount)
            / (10 ** collateral_token_parameters[token].decimals)
            * (collateral_token_parameters[token].collateral_factor if risk_adjusted else 1.0)
            * float(collateral_interest_rate_model[token])
            * prices[collateral_token_parameters[token].underlying_address]
            for token, token_amount in self.collateral.items()
        )

    def compute_debt_usd(
        self, 
        risk_adjusted: bool,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
        prices: Prices,
    ) -> float:
        return sum(
            float(token_amount)
            / (10 ** debt_token_parameters[token].decimals)
            / (debt_token_parameters[token].debt_factor if risk_adjusted else 1.0)
            * float(debt_interest_rate_model[token])
            * prices[debt_token_parameters[token].underlying_address]
            for token, token_amount in self.debt.items()
        )

    @abc.abstractmethod
    def compute_health_factor(self):
        pass

    @abc.abstractmethod
    def compute_debt_to_be_liquidated(self):
        pass

    def get_collateral_str(
        self,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
    ) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / (10 ** collateral_token_parameters[token].decimals) * collateral_interest_rate_model[token], 4)}"
            for token, token_amount in self.collateral.items()
            if token_amount > decimal.Decimal("0")
        )

    def get_debt_str(
        self,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
    ) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / (10 ** debt_token_parameters[token].decimals) * debt_interest_rate_model[token], 4)}"
            for token, token_amount in self.debt.items()
            if token_amount > decimal.Decimal("0")
        )

    def has_collateral(self) -> bool:
        return any(token_amount for token_amount in self.collateral.values())

    def has_debt(self) -> bool:
        return any(token_amount for token_amount in self.debt.values())
