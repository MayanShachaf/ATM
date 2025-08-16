from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.endpoints import router as api_router
from db import database

#this function initializes the database connection when the application starts
@asynccontextmanager
async def lifespan(_app: FastAPI):
    await database.initialize_database()
    yield

app = FastAPI(lifespan=lifespan)

# Include the API router
app.include_router(api_router, prefix="")

