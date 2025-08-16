from db import database


async def get_balance(account_number: str) -> float:
    try:
        return await database.get_balance(account_number)
    except database.AccountNotFoundError:
        # Account not found, return 0 balance
        return 0


async def deposit(account_number: str, amount: float) -> float:
    return await database.deposit(account_number, amount)


async def withdraw(account_number: str, amount: float) -> float:
    return await database.withdraw(account_number, amount)
