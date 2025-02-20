import redis.asyncio as redis
from fastapi import FastAPI, Depends, APIRouter
from contextlib import asynccontextmanager
from functools import lru_cache
from sqlmodel import create_engine
from init_db import init_db
from lib.app.common import get_settings, get_redis
from routes.auth_routes import router
from routes.user_routes import router as user_router
from routes.admin_routes import router as admin_router
from routes.account_routes import router as account_router
from routes.trial_routes import router as trial_router
from routes.agent_routes import router as agent_router
from routes.attachment_routes import router as attachment_router
from typing import Annotated


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_engine(
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
    )
    init_db(engine, settings.admin_password)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/auth", tags=["Auth"])
app.include_router(user_router, prefix="/users", tags=["User"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(account_router, prefix="/accounts", tags=["Account"])
app.include_router(trial_router, prefix="/trials", tags=["Trial"])
app.include_router(agent_router, prefix="/agents", tags=["Agent"])
app.include_router(attachment_router, prefix="/attachments", tags=["Attachment"])

@app.get("/")
def read_root(settings = Depends(get_settings)):
    return {"message": "Hello, World!", "postgres_db": settings.postgres_db}

@app.get("/ping")
async def ping_redis(redis_connection: Annotated[redis.Redis, Depends(get_redis)]):
    pong = await redis_connection.ping()
    return {"message": "Pong!" if pong else "Failed to ping Redis"}
