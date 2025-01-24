from fastapi import APIRouter, HTTPException
from fastapi import Depends
from schemas.schemas import UserLoanByWalletParams, UserLoanByWalletResponse
import json
import pandas as pd

loan_router = APIRouter()

# def parse_json(data):
#     try:
#         parsed = json.loads(data.replace("'", '"'))
#         if not parsed:
#           parsed = {}
#         return parsed
#     except (json.JSONDecodeError, AttributeError, TypeError):
#         return {}

def parse_json(data):
    if isinstance(data, str):
        try:
            return json.loads(data.replace("'", '"'))
        except json.JSONDecodeError:
            pass
    return {}


@loan_router.get("/loan_data_by_wallet_id", response_model=UserLoanByWalletResponse)
async def get_loans_by_wallet_id(params: UserLoanByWalletParams = Depends()):
  """
    Retrieve loan data associated with a specific wallet ID.

    endpoint allows users to query their loan details by providing a 
    wallet ID and optional block range parameters. The response includes 
    information about the user's collateral, debt, and deposits across 
    the specified loan protocol.
    
    Args:
      wallet_id (str): The wallet ID of the user
      protocol_name (str): The name of the loan protocol
      start_block (int): The start block
      end_block (int): The end block
    
    Returns:
      UserLoanByWalletResponse: User loan Information
      
    Raises:
      HTTPException: If address is not mapped
  """
  
  try:
    data_path = "apps/sdk/mock_data.csv"
    df = pd.read_csv(data_path)
    
    filter_df = df[
      (df['user'] == params.wallet_id) & 
      (df['protocol_id'] == params.protocol_name)
    ]
    
    if params.start_block is not None:
      filter_df = filter_df[filter_df['block'] >= params.start_block]
      
    if params.end_block is not None:
      filter_df = filter_df[filter_df['block'] <= params.end_block]
      
    if filter_df.empty:
      raise HTTPException(
        status_code=404,
        detail=f"No data found for user {params.wallet_id} in protocol {params.protocol_name}"
      )
      
    latest_entry = filter_df.sort_values('timestamp', ascending=False).iloc[0]

    collateral = parse_json(latest_entry['collateral'])
    debt = parse_json(latest_entry['debt'])
    deposit = parse_json(latest_entry['deposit'])
    
    return UserLoanByWalletResponse(
      wallet_id=params.wallet_id,
      protocol_name=params.protocol_name,
      collateral=collateral,
      debt=debt,
      deposit=deposit
    )
    
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error: {str(e)}"
    )  
