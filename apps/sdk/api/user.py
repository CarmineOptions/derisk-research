import csv
from fastapi import FastAPI, HTTPException
from typing import Optional, Dict
from pydantic import BaseModel

from schemas import mock_data.csv

app = FastAPI()

# Read CSV and return mock data
def read_csv_data():
    debt_data = {}
    with open('mock_data.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            wallet_id = row['user']
            protocol_id = row['protocol_id']
            debt = row['collateral']

            if wallet_id not in debt_data:
                debt_data[wallet_id] = []
    
            # Append the protocol and collateral for this wallet
            debt_data[wallet_id].append({
                'protocol_id': protocol_id,
                'collateral': debt
            })
    
    return debt_data

# Load mock data from CSV
mock_debt_data = read_csv_data()

# Response model for the new endpoint
class DebtResponseModel(BaseModel):
    wallet_id: str
    protocol_name: str
    debt: Dict[str, float]

@app.get("/get_user_debt", response_model=DebtResponseModel)
async def get_user_debt(wallet_id: str, protocol_name: str):
    # Check if the wallet_id exists
    if wallet_id in mock_debt_data:
        # Check if the protocol_name exists for the provided wallet_id
        for protocol in mock_debt_data[wallet_id]:
            if protocol['protocol_id'] == protocol_name:
                # Return the matching debt info
                return DebtResponseModel(wallet_id=wallet_id, protocol_name=protocol_name, debt=protocol['collateral'])
        # If no matching protocol_name is found for the wallet_id
        raise HTTPException(status_code=404, detail="Protocol not found")
    else:
        raise HTTPException(status_code=404, detail="Wallet not found")
