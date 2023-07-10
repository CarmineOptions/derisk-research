mapping = {
    "ETH": {
        "borrow_factor": 1
        "bonus": 0.1
    },
    "USDC": {
        "borrow_factor": 1
        "bonus": 0.1
    },
    "WBTC": {
        "borrow_factor": 0.91
        "bonus": 0.15
    }, 
    "USDT": {
        "borrow_factor": 0.91
        "bonus": 0.1
    }, 
    "DAI": {
        "borrow_factor": 0.91
        "bonus": 0.1 
    }
}

user_input = input("Enter ETH, USDC, WBTC, USDT, or DAI: ")

if user_input in mapping: 
    borrow_factor = mapping[user_input]["borrow_factor"]
    bonus = mapping[user_input]["bonus"]
else:
    print("Entered value not found.")

#borrow_factor = 0.8
#bonus = 0.1

ASSET_PRICE_0 = 1900

colateral_0 = 1
loan_0 = 1500

# 1.0133333333333334
health_0 = colateral_0 * ASSET_PRICE_0 * borrow_factor / loan_0

print("health at the start", health_0)

ASSET_PRICE_1 = 1800

# 0.96
health_1 = colateral_0 * ASSET_PRICE_1 * borrow_factor / loan_0

print("health after price moved", health_1)

# simulating liquidation of random sizes
for colateral_liquidated in [0.3, 0.35, 0.4, 0.45, 0.5]:
    health_2 = ((colateral_0 - colateral_liquidated) * ASSET_PRICE_1 * borrow_factor) / (
        loan_0 - ASSET_PRICE_1 * (colateral_liquidated * (1 - bonus))
    )
    gain = ASSET_PRICE_1 * colateral_liquidated * bonus
    print("liquidating", colateral_liquidated, "\nhealth:", health_2, "\ngain:", gain)


colateral_liquidated = (loan_0 - colateral_0 * ASSET_PRICE_1 * borrow_factor) / (
    ASSET_PRICE_1 * (1 - bonus) - ASSET_PRICE_1 * borrow_factor
)
health_3 = ((colateral_0 - colateral_liquidated) * ASSET_PRICE_1 * borrow_factor) / (
    loan_0 - ASSET_PRICE_1 * (colateral_liquidated * (1 - bonus))
)
gain = ASSET_PRICE_1 * colateral_liquidated * bonus

print("calculated liquidation")
print("liquidating", colateral_liquidated, "\nhealth:", health_3, "\ngain:", gain)