from fastapi import FastAPI, Depends
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    rabbitmq_password: str = Field(alias="RABBITMQ_USER")
    rabbitmq_user: str = Field(alias="RABBITMQ_PASSWORD")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    redis_password: str = Field(alias="REDIS_PASSWORD")

@lru_cache()
def get_settings():
    return Settings()

app = FastAPI()

@app.get("/")
def read_root(settings = Depends(get_settings)):
    return {"message": "Hello, World!", "postgres_db": settings.postgres_db}
