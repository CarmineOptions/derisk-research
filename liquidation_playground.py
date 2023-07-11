from classes import get_prices, __init__, to_dollars
import decimal

# Asset types and associated variables: 
mapping = {
    "ETH": {
        "collateral_factor": decimal.Decimal(0.8),
        "bonus": decimal.Decimal(0.1),
        "borrow_factor": decimal.Decimal(1.0)
    },
    "USDC": {
        "collateral_factor": decimal.Decimal(0.8),
        "bonus": decimal.Decimal(0.1),
        "borrow_factor": decimal.Decimal(1)
    },
    "wBTC": {
        "collateral_factor": decimal.Decimal(0.7),
        "bonus": decimal.Decimal(0.15), 
        "borrow_factor": decimal.Decimal(0.91)
    }, 
    "USDT": {
        "collateral_factor": decimal.Decimal(0.7),
        "bonus": decimal.Decimal(0.1), 
        "borrow_factor": decimal.Decimal(0.91)
    }, 
    "DAI": {
        "collateral_factor": decimal.Decimal(0.7),
        "bonus": decimal.Decimal(0.1), 
        "borrow_factor": (0.91) 
    }
}

# Input 1:  
collateral_input = input("Enter Collateral Type {ETH, USDC, wBTC, USDT, or DAI}: ")

# Input 2:  
collateral_amount = input("Enter Quantitative Amount: ")

# Input 3: 
loan_input = input("Enter Loan Amount in USD: ")


# Check to see if inputted value exists: 
if collateral_input in mapping: 
    collateral_factor = mapping[collateral_input]["collateral_factor"]
    bonus = mapping[collateral_input]["bonus"]
else:
    print("Entered value not found.")
    

# ~Variables~ 

# Collateral Amount in Asset Price 
C = collateral_amount * get_prices(collateral_input)

# Collateral Liquidated 
CL = (loan_input - C * to_dollars(collateral_input) * collateral_factor) / (
    (to_dollars(collateral_input) * (1 - bonus)) - (to_dollars(collateral_input) * collateral_factor) 
)
# Price of Asset in USD
E = to_dollars(collateral_input) 



# Health: Calculated as collateral value divided by loan value 
def health():
    health_0 = (C * E * collateral_factor) / loan_input 
    print("Health", health_0)


# Health AFTER Liquidation 
def health_after_liquidation():
    health_1 = ((C - CL) * E * collateral_factor) / (loan_input - CL * E * (1 + bonus))

#Simulating 
for collateral_liquidated in [0.3, 0.35, 0.4, 0.45, 0.5]:
    health_2 = ((C - CL) * E * collateral_factor) / (loan_input - E * (CL * (1 + bonus)))
    gain = (collateral_amount * get_prices(collateral_input)) * collateral_liquidated * bonus
    print("liquidating", collateral_liquidated, "\nhealth:", health_2, "\ngain:", gain)


