from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Code Review Agent"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./data/code_review_agent.db"
    cors_origins: str = "http://localhost:8000,http://localhost:5173"

    hindsight_api_url: str = "http://localhost:8888"
    hindsight_api_key: str = ""

    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.15

    github_token: str = ""
    demo_mode: bool = False
    max_diff_chars: int = 60000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
