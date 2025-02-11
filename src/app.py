from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, SQLModel, create_engine
from init_db import init_db

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    admin_password: str = Field("ADMIN_PASSWORD")
    rabbitmq_password: str = Field(alias="RABBITMQ_USER")
    rabbitmq_user: str = Field(alias="RABBITMQ_PASSWORD")
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    redis_password: str = Field(alias="REDIS_PASSWORD")

@lru_cache()
def get_settings():
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_engine(
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
    )
    init_db(engine, settings.admin_password)
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root(settings = Depends(get_settings)):
    return {"message": "Hello, World!", "postgres_db": settings.postgres_db}
