from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_referer: str = "http://localhost"
    openrouter_app_title: str = "bank-transaction-categorizer-mvp"
    llm_enabled: bool = False
    llm_batch_size: int = 20
    llm_confidence_threshold: float = 0.74
    database_url: str = "postgresql+psycopg://banktx:banktx_dev_password@postgres:5432/banktx"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
