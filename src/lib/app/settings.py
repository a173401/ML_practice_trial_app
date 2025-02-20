from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', frozen=True, extra='ignore')
    admin_password: str = Field("ADMIN_PASSWORD")
    rabbitmq_host: str = Field(alias="RABBITMQ_HOST")
    rabbitmq_password: str = Field(alias="RABBITMQ_PASSWORD")
    rabbitmq_user: str = Field(alias="RABBITMQ_USER")
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    redis_password: str = Field(alias="REDIS_PASSWORD")
    redis_host: str = Field(alias="REDIS_HOST")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_bucket: str = Field(alias="MINIO_BUCKET")

class WorkerSettings(Settings):
    bothub_token: str = Field("BOTHUB_TOKEN")
    bothub_chat_id: str = Field("BOTHUB_CHAT_ID")

class SystemConfig(BaseModel):
    cost_per_request: float = 1.0
    max_rounds: int = 5
    min_balance: float = 0.0
    default_credits: float = 50.0
