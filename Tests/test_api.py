import os
import sys
from fastapi.testclient import TestClient

# Ensure the directory above this Tests folder is on sys.path so we can import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # main.py is now importable from the project root

# Create a test client for the FastAPI app
# This allows us to make requests to the API endpoints in our tests
client = TestClient(app)

# Test deosit and then balance retrieval
def test_deposit_then_get_balance():
    account = "112"
    resp = client.post(f"/accounts/{account}/deposit", json={"amount": 50.0})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 50.0
    bal_resp = client.get(f"/accounts/{account}/balance")
    assert bal_resp.status_code == 200
    assert bal_resp.json()["balance"] == 50.0


#Test deposit, withdraw and then get balance
def test_deposit_withdraw_then_balance():
    account = "223"
    resp = client.post(f"/accounts/{account}/deposit", json={"amount": 50.0})
    assert resp.status_code == 200
    resp = client.post(f"/accounts/{account}/withdraw", json={"amount": 20.0})
    assert resp.status_code == 200
    bal_resp = client.get(f"/accounts/{account}/balance")
    assert bal_resp.status_code == 200
    assert bal_resp.json()["balance"] == 30.0


#Test withdraw with insufficient funds
def test_overdraft_error():
    account = "334"
    resp = client.post(f"/accounts/{account}/withdraw", json={"amount": 1500.0})
    assert resp.status_code == 400


#Test balance for account that does not exist in db
def test_new_account_get_balance():
    account = "445"
    resp = client.get(f"/accounts/{account}/balance")
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0

