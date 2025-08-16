from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveFloat

from db.database import InsufficientFundsError
from logic import operations

router = APIRouter()


@router.get("/{account_number}/balance")
async def get_balance_api(account_number: str):
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
