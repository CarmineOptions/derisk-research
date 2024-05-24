from web_app.utils.abstractions import AbstractionAPIConnector


class HaikoAPIConnector(AbstractionAPIConnector):
    API_URL = "https://app.haiko.xyz/api/v1"

    @classmethod
    def get_token_markets(cls):
        endpoint = "/markets?network=mainnet"
        return cls.send_get_request(endpoint)

    @classmethod
    def get_supported_tokens(cls, existing_only: bool = True) -> dict:
        if not isinstance(existing_only, bool):
            raise ValueError("Existing only parameter must be a bool")
        endpoint = f"/tokens?network=mainnet&existingOnly={existing_only}"
        return cls.send_get_request(endpoint)
