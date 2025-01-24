from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import pandas as pd
import json
from data_handler.db.schemas import ResponseModel

app = FastAPI()  

file_path = "../mock_data.csv"
mock_data = pd.read_csv(file_path)

def parse_debt_data(row):
    try:
        return json.loads(row) if row.strip() else {}
    except json.JSONDecodeError:
        return {}

mock_data["debt"] = mock_data["debt"].apply(parse_debt_data)


debt_data = {}
for _, row in mock_data.iterrows():
    wallet_id = row["user"]
    protocol = row["protocol_id"]
    debt = row["debt"]
    if wallet_id not in debt_data:
        debt_data[wallet_id] = {}
    debt_data[wallet_id][protocol] = debt

@app.get("/get_user_debt", response_model=ResponseModel)
def get_user_debt(wallet_id: str, protocol_name: str):
    """
    Endpoint to get the debt details of a user for a specific protocol.
    
    Args:
        wallet_id (str): The wallet ID of the user.
        protocol_name (str): The protocol name for which debt details are requested.

    Returns:
        ResponseModel: The debt details including wallet ID, protocol name, and token-value pairs.
    """
    wallet_data = debt_data.get(wallet_id)
    debt_data = debt_data.get(protocol)
    return {"wallet_id": wallet_id, "protocol": protocol, "debt": debt_data}
    if not wallet_data:
        return {"wallet_id": wallet_id, "protocol_name": protocol_name, "debt": {}}

    protocol_data = wallet_data.get(protocol_name)
    if not protocol_data:
        return {"wallet_id": wallet_id, "protocol_name": protocol_name, "debt": {}}

    return {"wallet_id": wallet_id, "protocol_name": protocol_name, "debt": protocol_data}