from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql://permitflow:permitflow@localhost:5432/permitflow"
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-v4-pro"
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-v4"
    embedding_dimensions: int = Field(default=1536, ge=64, le=2048)
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_encrypt_key: str = ""
    jira_base_url: str = "https://jira.example.com"
    jira_email: str = ""
    jira_api_token: str = ""
    it_service_desk_url: str = "https://jira.example.com/servicedesk"
    session_ttl_minutes: int = Field(default=30, ge=1)
    log_level: str = "INFO"
    admin_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
