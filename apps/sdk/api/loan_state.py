from fastapi import APIRouter, HTTPException
from schemas.schemas import UserLoanByWalletParams, UserLoanByWalletResponse
import pandas as pd

loan_router = APIRouter

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
    
    collateral_map = {}
    debt_map = {}
    deposit_map ={}
    
    for _, row in filter_df.iterrows():
      for token, value in row['collateral'].items():
        collateral_map[token] = collateral_map.get(token, 0) + value
      for token, value in row['debt'].items():
        debt_map[token] = debt_map.get(token, 0) + value
      for token, value in row['deposit'].items():
        deposit_map[token] = deposit_map.get(token, 0) + value

    return UserLoanByWalletResponse(
      wallet_id=params.wallet_id,
      protocol_name=params.protocol_name,
      collateral=collateral_map,
      debt=debt_map,
      deposit=deposit_map
    )
    
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error: {str(e)}"
    )  
  