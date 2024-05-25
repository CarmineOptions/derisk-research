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


class HaikoBlastAPIConnector(AbstractionAPIConnector):
    API_URL = "https://starknet-mainnet.blastapi.io"
    PROJECT_ID = "a419bd5a-ec9e-40a7-93a4-d16467fb79b3"

    @classmethod
    def _post_request_builder(cls, call_method: str, params: dict):
        if not isinstance(call_method, str) or not isinstance(params, dict):
            raise ValueError("Call method must be a string and params must be a dict")
        body = {
            "jsonrpc": "2.0", "method": call_method, "params": params, "id": 0
        }
        endpoint = f"/{cls.PROJECT_ID}"
        return cls.send_post_request(endpoint, json=body)

    @classmethod
    def get_block_info(cls) -> dict:
        return cls._post_request_builder("starknet_getBlockWithTxHashes", params={"block_id": "latest"})
