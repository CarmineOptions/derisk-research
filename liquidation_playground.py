import dataclasses
import classes 
import decimal

prices = classes.Prices()
# Asset types and associated variables: 
@dataclasses.dataclass 
class Token:  
    token: str 
    collateral_factor: decimal
    bonus: decimal
    
token_information: Dict[str, Token] = {
        "ETH": Token('ETH', decimal.Decimal(str(0.8)), decimal.Decimal(str(0.1))),
        "USDC": Token('USDC', decimal.Decimal(str(0.8)), decimal.Decimal(str(0.1))),
        "wBTC": Token('wBTC', decimal.Decimal(str(0.7)), decimal.Decimal(str(0.15))),
        "USDT": Token('USDT', decimal.Decimal(str(0.7)), decimal.Decimal(str(0.1))),
        "DAI": Token('DAI', decimal.Decimal(str(0.7)), decimal.Decimal(str(0.1)))    
}
        

# Input 1:  
collateral_input = input("Enter Collateral Type {ETH, USDC, wBTC, USDT, or DAI}: ")

# Input 2:  
collateral_amount = input("Enter Quantitative Amount: ")

# Input 3: 
loan_input = input("Enter Loan Amount in USD: ")


# Check to see if inputted value exists: 
if collateral_input in token_information: 
    collateral_factor = token_information[collateral_input]["collateral_factor"]
    bonus = token_information[collateral_input]["bonus"]
else:
    print("Entered value not found.")
    

# ~Variables~ 

# Collateral Amount in Asset Price (in USD)
C = collateral_amount * prices[collateral_input]

# Collateral Liquidated 
CL = (loan_input - C * prices.to_dollars(collateral_input) * collateral_factor) / (
    (prices.to_dollars(collateral_input) * (1 - bonus)) - (prices.to_dollars(collateral_input) * collateral_factor) 
)
# Price of Asset in USD
E = prices.to_dollars(collateral_input) 



# Health: Calculated as collateral value divided by loan value 
def health():
    health_0 = (C * E * collateral_factor) / loan_input 
    print("Health", health_0)


# Health AFTER Liquidation 
def health_after_liquidation():
    health_1 = ((C - CL) * E * collateral_factor) / (loan_input - CL * E * (1 + bonus))

#Simulating 
for ex_collateral_liquidated in [0.3, 0.35, 0.4, 0.45, 0.5]:
    health_2 = ((C - CL) * E * collateral_factor) / (loan_input - E * (CL * (1 + bonus)))
    gain = (collateral_amount * prices.get_prices(collateral_input)) * ex_collateral_liquidated * bonus
    print("liquidating", ex_collateral_liquidated, "\nhealth:", health_2, "\ngain:", gain)


