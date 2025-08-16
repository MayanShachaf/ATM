# ATM API

# Overview

This repository contains a simple asynchronous ATM service implemented in Python. It exposes a REST API using FastAPI that allows clients to:

- Check the balance of an account.
- Deposit money into an account.
- Withdraw money from an account, subject to a configurable debt limit.

The service uses SQLite as the storage layer and the aiosqlite library for asynchronous database access. All database operations are performed in async functions to ensure that the API remains responsive even when many clients are connected.

# How to run

1.Clone the repository and create a virtual environment:
```
git clone https://github.com/MayanShachaf/ATM.git
cd ATM
python3 -m venv venv
source venv/bin/activate
```
2.Install dependencies from requirements.txt:
```
pip install -r requirements.txt
```
3.Create a .env file (optional) to override default configuration. The service supports these environment variables:
- DB_PATH – file name of the SQLite database; defaults to atm.db.
- MAX_DEBT – maximum negative balance allowed (i.e., overdraft limit); defaults to 1000.
Example .env file:
```
DB_PATH=/tmp/atm.db
MAX_DEBT=500
```
4.Start the API using Uvicorn. The project defines the FastAPI app in main.py as app.
Run:
```
uvicorn main:app --reload --port 8000
```
When the server starts, it will call initialize_database() inside the lifespan context of FastAPI to create the accounts table if it does not already exist.

5.Test the API. You can access the interactive documentation at http://localhost:8000/docs. Below are simple cURL examples:

-Check API health:
```
curl http://localhost:8000/is_alive
# {"active":"true"}
```
-Check account balance (returns 0 if the account does not exist):
```
curl http://localhost:8000/accounts/1234/balance
# {"account_number":"1234","balance":0}
```
-Deposit money:
```
curl -X POST http://localhost:8000/accounts/1234/deposit      -H 'Content-Type: application/json'      -d '{"amount": 150.5}'
# {"account_number":"1234","deposited_amount":150.5,"balance":150.5,"status":"success"}
```

-Withdraw money (the maximum overdraft is controlled by MAX_DEBT; on insufficient funds it returns HTTP 400):
```
curl -X POST http://localhost:8000/accounts/1234/withdraw      -H 'Content-Type: application/json'      -d '{"amount": 200}'
# {"account_number":"1234","withdrawn_amount":200,"balance":-49.5,"status":"success"}
```

-If the withdrawal would exceed the allowed debt limit, the API returns:

{"detail": "Insufficient funds for withdrawal"}


# Project structure

```
ATM/
├── api/              # FastAPI routers and request/response models
│   ├── accounts.py   # Endpoints for balance, deposit and withdraw
│   └── endpoints.py  # Main router, includes health check and account routes
├── db/               # Database layer
│   └── database.py   # Async functions for accessing SQLite
├── logic/            # Business logic layer
│   └── operations.py # Orchestrates database calls and handles defaults
├── main.py           # Entry point creating the FastAPI app
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation (you are reading it)
```

# API layer (api/accounts/)

The API layer exposes REST endpoints using FastAPI. In api/accounts.py, three endpoints are defined:

- GET /{account_number}/balance – returns the current balance for the given account; if the account does not exist it returns a balance of 0.
- POST /{account_number}/withdraw – withdraws a positive amount from the account. It returns the updated balance and raises an HTTP 400 error when the resulting balance would exceed the allowed debt.
- POST /{account_number}/deposit – deposits a positive amount into the account and returns the updated balance.

The root router api/endpoints.py registers a health check at /is_alive and includes the account routes under the /accounts prefix.

# Logic layer (logic/)

The logic layer sits between the API and the database. It contains simple asynchronous functions in operations.py that call the database layer. For example, get_balance calls database.get_balance and returns 0 if the account is not found. This separation makes it easy to add further business rules without changing the API or database code.

# Database layer (db/)

The database layer uses aiosqlite to communicate with SQLite. It defines custom exceptions (AccountNotFoundError and InsufficientFundsError) and provides functions for initializing the database and updating balances. Key points:

- Database initialization – initialize_database() is called once at startup and creates the accounts table with two columns: account_number (primary key) and balance. A check constraint ensures that the balance never drops below -MAX_DEBT.
- Single operation per connection – each database function uses an async with aiosqlite.connect block. A fresh connection is opened for each request and closed immediately afterwards. For updates we also specify a timeout (default 5 seconds) to avoid indefinite waits in case of concurrent writes.
- Atomic upsert – deposits and withdrawals call _update_balance, which uses an INSERT ON CONFLICT DO UPDATE statement to atomically insert a new account or update the existing balance. The upsert returns the new balance. If the update would violate the balance >= -MAX_DEBT constraint, aiosqlite raises an IntegrityError; this is caught and converted into an InsufficientFundsError.

# Why use aiosqlite and database-level locking?

To support multiple concurrent requests (for example, several clients depositing or withdrawing at once), we needed a data store that can handle concurrency safely. There were two design options:

- In‑memory data structure with custom locks.
 I could store balances in a Python dictionary and use threading-Lock or asyncio-Lock to ensure only one coroutine modifies a given account at a time. This would avoid database overhead but requires implementing our own locking logic (e.g., per‑account locks). The downside is that locks introduce complexity, especially when the service scales or runs across multiple processes. Persistent storage would also be needed to retain balances when the service restarts.

- Use a database with atomic operations.
 I chose SQLite with aiosqlite. SQLite is lightweight and supports atomic upsert operations. aiosqlite provides an async interface so the event loop does not block. SQLite’s internal locking ensures that only one write happens at a time, avoiding race conditions without explicit locks. The INSERT ON CONFLICT DO UPDATE statement updates the balance in one atomic step, so concurrent deposits or withdrawals will not corrupt the balance. If an update would violate the overdraft limit (balance >= -MAX_DEBT), SQLite raises an integrity error which we map to a 400 error. Using a database also means balances persist across restarts. The trade‑off is a slight performance penalty due to disk access and the per‑request connection overhead (mitigated by the small size of the database and the use of a 5‑second timeout on connections).

In summary, I preferred database‑level locking for its simplicity and reliability. SQLite handles concurrency and atomicity for us, and aiosqlite ensures the API remains non‑blocking.

# Database schema and debt limit

The accounts table is created with this schema:
```
CREATE TABLE IF NOT EXISTS accounts (
    account_number TEXT PRIMARY KEY,
    balance REAL NOT NULL DEFAULT 0.0 CHECK (balance >= -{MAX_DEBT})
);
```
-Each account_number is a string that uniquely identifies an account.

-The balance is a real number. The CHECK constraint prevents the balance from going below  -MAX_DEBT, where MAX_DEBT is defined by an environment variable (default 1000).

-New accounts are created implicitly when you deposit or withdraw for the first time; the upsert will insert the account if it does not already exist.

The debt limit is chosen as a minimum debt rather than a fixed overdraft. By default you can overdraw up to –1000 units; you can adjust this by setting MAX_DEBT in your .env file.

# Environment variables

The project reads its configuration from environment variables using python-dotenv (loaded at the top of db/database.py). These variables are optional:

- DB_PATH: Path to the SQLite database file (default atm.db)
- MAX_DEBT: Maximum negative balance allowed. The balance cannot drop below -MAX_DEBT and withdrawals beyond this limit raise an error (default 1000)
- UVICORN_PORT: Port on which to run the server (used when running via Docker or in a deployment script)

To change any of these, create a .env file in the project root or set the variables in your shell before starting the server.

# API endpoints and responses

## GET /is_alive

Simple health‑check. Returns { "active": "true" }.

## GET /accounts/{account_number}/balance

Retrieve the current balance. If the account does not exist, the logic layer returns a balance of 0.

Successful response (200):

```
{"account_number":"1234","balance":0.0}
```

Unexpected error (500): returns { "detail": "Unable to retrieve balance" }.

## POST /accounts/{account_number}/deposit

Deposit money into an account. The request body must contain a positive amount.

Request body:

```
{ "amount": 50.0 }
```

Successful response (200):

```
{"account_number":"1234","deposited_amount":50.0,"balance":150.5,"status":"success"}
```

Validation error (422): if amount is missing or not positive.

Unexpected error (500): returns { "detail": "Unable to process deposit" }.

## POST /accounts/{account_number}/withdraw

Withdraw money from an account. The request body must contain a positive amount. If the resulting balance would be less than -MAX_DEBT, an error is raised.

Request body:

```
{ "amount": 200.0 }
```

Successful response (200):

```
{"account_number":"1234","withdrawn_amount":200.0,"balance":-49.5,"status":"success"}
```

Insufficient funds (400):

```
{"detail":"Insufficient funds for withdrawal"}
```

Validation error (422): if amount is missing or not positive.

Unexpected error (500): returns { "detail": "Unable to process withdrawal" }.

# Concurrency considerations and challenges

Because this service needs to handle concurrent deposits and withdrawals, careful thought went into the design:

- Asynchronous I/O – all API handlers and database operations are async. This allows FastAPI to serve many clients concurrently without blocking the event loop.
- Atomic updates – the _update_balance function performs an upsert using INSERT ON CONFLICT DO UPDATE. This SQL statement either inserts a new row or updates the existing balance in one step, preventing race conditions even when multiple clients write concurrently.
- Database constraints – the CHECK constraint ensures the balance never drops below -MAX_DEBT. Violations raise an IntegrityError, which we translate into a user‑friendly error.
- Per‑request connections – each operation opens a new connection with a small timeout (timeout=5 seconds). SQLite locks the database during writes; using separate connections with a timeout prevents the application from hanging indefinitely.

# Why not a custom locking mechanism?

Early in the design, there was a choice between using a shared in‑memory state with explicit locks and using a database. Implementing custom locks could improve performance but introduces complexity:

- You must ensure that locks cover all code paths where the balance changes. Forgetting to acquire or release a lock leads to corruption or deadlocks.
- Running the service with multiple worker processes (e.g., behind a load balancer) requires inter‑process locks or a distributed lock system.

By choosing a database, we delegate concurrency control to SQLite. SQLite’s write‑ahead logging and internal locking guarantee that only one write transaction occurs at a time, and the ON CONFLICT UPDATE upsert ensures atomicity. This greatly simplifies the code while still handling concurrent access safely. If the project grows and needs higher throughput, the same design can migrate to PostgreSQL or another relational database without changing the API.

# Conclusion

This ATM API provides a small but complete example of building an asynchronous web service in Python. It shows how to structure a FastAPI application into API, logic, and database layers, how to use aiosqlite for simple persistence, and how to handle concurrency using database transactions rather than custom locks. The service is configurable via environment variables and comes with interactive documentation for easy testing. Feel free to extend it with additional features such as account creation, transfer between accounts, authentication or integration with a more scalable database.

--------------

# Hosting: the server-side deploy in Render

I use Render to deploy this small API because it offers push-to-deploy from Git, always-on containers, built-in HTTPS and env vars, easy scaling/logs, and zero server management.

API (RENDER): https://atm-0ofb.onrender.com
API DOCS : https://atm-0ofb.onrender.com/docs   

