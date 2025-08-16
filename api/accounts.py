from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveFloat

from db.database import InsufficientFundsError
from logic import operations

router = APIRouter()

#GET balance endpoint 
@router.get("/{account_number}/balance")
async def get_balance_api(account_number: str):
    """
    Retrieve the balance of a specific account.

    Args:
        account_number (str): The account number to retrieve the balance for.

    Returns:
        object: A object containing the account number and its current balance.
        if the account does not exists, we retun 0 as the balance.
        If an unexpected error occurs, a 500 HTTPException is raised.
    """
    try:
        current_balance = await operations.get_balance(account_number)
        return {"account_number": account_number, "balance": current_balance}
    except Exception:
        # Unexpected error occurred while retrieving the balance
        raise HTTPException(status_code=500, detail="Unable to retrieve balance")


class WithdrawBody(BaseModel):
    amount: PositiveFloat = Field(..., description="> 0")

@router.post("/{account_number}/withdraw")
async def withdraw_money_api(account_number: str, data: WithdrawBody):
    '''
    this api is used to withdraw money from an account.
    args:
        account_number (str): The account number to withdraw from.
        data (WithdrawBody): The amount to withdraw, must be greater than zero.

    Returns:
        object: A object containing the account number, withdrawn amount, and remaining balance.
        If the withdrawal fails due to insufficient funds, a 400 HTTPException is raised.
        If an unexpected error occurs, a 500 HTTPException is raised.
    limits: maximum debt is MAX_DEBT, which is defined in the logic/operations.py file. 

    '''
    try:
        balance = await  operations.withdraw(account_number, data.amount)
        return {
            "account_number": account_number,
            "withdrawn_amount": data.amount,
            "balance": balance,
            "status": "success"
        }
    except InsufficientFundsError:
        raise HTTPException(status_code=400, detail="Insufficient funds for withdrawal")
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to process withdrawal")


class DepositBody(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit must be greater than zero.")


@router.post("/{account_number}/deposit")
async def deposit_money_api(account_number: str, data: DepositBody):
    """
    Deposit money into a specific account.
    
    Args:
        account_number (str): The account number to deposit into.
        data (DepositBody): The amount to deposit, must be greater than zero.
        
    Returns:
        object: A object containing the account number, deposited amount, and updated balance.
        If the deposit fails due to an unexpected error, a 500 HTTPException is raised.
        
        """
    
    try:
        balance = await operations.deposit(account_number, data.amount)

        return {
            "account_number": account_number,
            "deposited_amount": data.amount,
            "balance": balance,
            "status": "success"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to process deposit")
