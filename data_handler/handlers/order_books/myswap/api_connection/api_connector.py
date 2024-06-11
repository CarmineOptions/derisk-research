from web_app.utils.abstractions import AbstractionAPIConnector


class MySwapAPIConnector(AbstractionAPIConnector):
    API_URL = "https://myswap-cl-charts.s3.amazonaws.com"

    @classmethod
    def get_pools_data(cls) -> dict:
        return cls.send_get_request("/data/pools/all.json")
