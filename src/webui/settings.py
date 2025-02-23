from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class WebSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', frozen=True, extra='ignore')
    backend_url: str = Field(alias="BACKEND_URL")
