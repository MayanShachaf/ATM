from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.endpoints import router as api_router
from db import database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await database.initialize_database()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix="")

