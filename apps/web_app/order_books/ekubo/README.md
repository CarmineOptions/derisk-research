# Ekubo

This folder contains all interaction with [Ekubo API](https://docs.ekubo.org/integration-guides/reference/ekubo-api/api-endpoints).

# Endpoints Documentation:
- [Get Pool Liquidity](docs/pool_liquidity.md) - Detailed information about liquidity in different pools.
- [Get Pools](docs/pools.md) - Detailed information about various pools.
- [Get Token Prices](docs/token_prices.md) - Information on how to retrieve current token prices.
- [Get List of Tokens](docs/token_lists.md) - List of tokens with detailed information.


# How to run 
In this folder: `ekubo` run next command
```bash
python main.py
```

# How to check quality of data
In this folder: `ekubo` run next command to see the histogram of the data
```bash
python manage.py histogram
```

## Histogram

To run the script to see histogram, use the following command:
!!! Pay attention, you should run it from `web_app` folder
```sh
python histogram.py  --type asks
```
or 
```sh
python histogram.py --type bids
```