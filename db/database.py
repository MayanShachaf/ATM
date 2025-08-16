import os
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "atm.db")
MAX_DEBT = os.getenv("MAX_DEBT", 1000)


class AccountNotFoundError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

async def initialize_database():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 0.0 CHECK (balance >= -{MAX_DEBT})
            )
        ''')
        await conn.commit()


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


async def update_balance(account_number: str, delta: float) -> float:
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


async def deposit(account_number: str, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")
    return await update_balance(account_number, amount)


async def withdraw(account_number: str, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Withdraw amount must be positive")
    return await update_balance(account_number, -amount)
