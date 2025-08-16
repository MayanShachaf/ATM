from db import database

# This module contains the logic for account operations such as balance retrieval, deposit, and withdrawal.


# Get the balance of an account from the database.
# If the account does not exist, it returns a balance of 0.
async def get_balance(account_number: str) -> float:
    try:
        return await database.get_balance(account_number)
    except database.AccountNotFoundError:
        # Account not found, return 0 balance
        return 0

# Deposit money into an account
async def deposit(account_number: str, amount: float) -> float:
    return await database.deposit(account_number, amount)

# Withdraw money from an account
# If the withdrawal amount exceeds the MAX_DEBT, it raises an InsufficientFundsError.
async def withdraw(account_number: str, amount: float) -> float:
    return await database.withdraw(account_number, amount)
