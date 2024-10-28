# Get List of Tokens

### Class Method
Retrieve a list of tokens by using:
`Ekubo.api_connector.EkuboAPIConnector.get_list_tokens()`

### Data Structure
This endpoint provides a list of tokens with detailed information. Each entry in the returned list is a dictionary containing:
- **name**: The name of the token, such as "Wrapped BTC".
  - Type: `str`
- **symbol**: The abbreviated symbol of the token, such as "WBTC".
  - Type: `int`
- **decimals**: The number of decimal places the token is divided into.
  - Type: `str`
- **l2_token_address**: The address of the token on layer 2, in hexadecimal format.
  - Type: `str`
- **sort_order**: An integer specifying the display order relative to other tokens; lower numbers appear first.
  - Type: `int`
- **total_supply**: The total supply of the token, if known. It can be 'None' if the total supply is not set or unlimited.
  - Type: `str`
- **logo_url**: A URL to the token's logo image.
  - Type: `str`