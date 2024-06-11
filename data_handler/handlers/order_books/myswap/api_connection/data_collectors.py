import requests


def braavos_get_tokens_prices(token_names_list: list[str]) -> list | dict:
    if not token_names_list:
        return {"error": "No tokens provided"}
    token_names = ",".join(token_names_list) if len(token_names_list) > 1 else token_names_list[0]
    params = {"symbols": token_names, "currency": "usd"}
    url = "https://price.braavos.app/prices"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
