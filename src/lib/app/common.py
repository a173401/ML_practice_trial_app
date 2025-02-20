import pika
import redis.asyncio as redis
from pika.adapters.blocking_connection import BlockingChannel
from functools import lru_cache
from sqlmodel import create_engine, Session
from sqlalchemy import Engine
from fastapi import Depends
from typing import Annotated
from .settings import Settings

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@lru_cache()
def get_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    settings = get_settings()
    engine = create_engine(
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
    )
    return engine

def get_session(engine: Annotated[Engine, Depends(get_engine)]) -> Session:
    with Session(engine) as session:
        yield session

async def get_redis(settings: Annotated[Settings, Depends(get_settings)]) -> redis.Redis:
    settings = get_settings()
    redis_connection = redis.Redis(host=settings.redis_host, port=6379, password=settings.redis_password)
    yield redis_connection
    await redis_connection.aclose()

def get_rabbitmq(settings: Annotated[Settings, Depends(get_settings)]) -> BlockingChannel:
    settings = get_settings()
    connection = pika.BlockingConnection(pika.ConnectionParameters(settings.rabbitmq_host, 
                                                                   credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)))
    channel = connection.channel()    
    yield channel
    connection.close()
