from api.accounts import router as accounts_router
from fastapi import  APIRouter

router = APIRouter()
# Health check endpoint to verify if the API is running
@router.get("/is_alive")
def is_alive():
    return {"active": "true"}

# Include the accounts router
router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
