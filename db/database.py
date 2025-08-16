import os
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "atm.db")
MAX_DEBT = os.getenv("MAX_DEBT", 1000)

# Database exceptions when account not found for get balance 
class AccountNotFoundError(Exception):
    pass


# Custom exception for insufficient funds during withdrawal
# This is raised when the withdrawal amount exceeds the allowed debt limit.
class InsufficientFundsError(Exception):
    pass


# Initialize the database and create the accounts table if it doesn't exist.
# This function is called when the application starts.
# It uses an async context manager to handle the database connection.
# define the datatbase schema: primary key is account_number, balance is a real number with a default of 0.0.
# It also checks that the balance does not go below -MAX_DEBT.
async def initialize_database():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 0.0 CHECK (balance >= -{MAX_DEBT})
            )
        ''')
        await conn.commit()


# Get the balance of an account from the database.
# If the account does not exist, it raises an AccountNotFoundError.
# This function is used in the logic layer to retrieve the balance of an account.
async def get_balance(account_number: str) -> float:
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (account_number,)
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            raise AccountNotFoundError()

        return row[0]


# Update the balance of an account by adding or subtracting a delta value.
# This function uses an UPSERT operation to either insert a new account or update the existing balance.
# It raises InsufficientFundsError if the resulting balance would be less than -MAX_DEBT.
# Returns the new balance after the operation.
async def _update_balance(account_number: str, delta: float) -> float:
    """
    Deposit or withdraw money (delta can be positive or negative).
    Uses UPSERT with CHECK constraint to prevent balance < -1000.
    Returns the new balance.
    """
    async with aiosqlite.connect(DB_PATH, timeout=5) as conn:
        try:
            async with conn.execute(
                """
                INSERT INTO accounts(account_number, balance)
                VALUES (?, ?)
                ON CONFLICT(account_number)
                DO UPDATE SET balance = accounts.balance + excluded.balance
                RETURNING balance
                """,
                (account_number, delta),
            ) as cursor:
                row = await cursor.fetchone()
                await conn.commit()
                return row[0] if row else None
        except aiosqlite.IntegrityError:
            raise InsufficientFundsError()

# Deposit money into an account
async def deposit(account_number: str, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")
    return await _update_balance(account_number, amount)

# Withdraw money from an account
async def withdraw(account_number: str, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Withdraw amount must be positive")
    return await _update_balance(account_number, -amount)
