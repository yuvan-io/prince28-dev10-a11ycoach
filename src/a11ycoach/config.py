"""All settings come from environment variables or a local .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "a11ycoach"
    app_env: Literal["local", "ci", "production"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    data_file: Path = Path("data/sample_records.json")
    database_url: str
    # The commit this image was built from. CI sets it (Dockerfile ARG GIT_SHA); locally "dev".
    git_sha: str = Field(default="dev", validation_alias="A11YCOACH_GIT_SHA")
    # LLM gateway (Day 8)
    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_primary_model: str = "gemini-3.8-flash"
    llm_fallback_model: str = "openai/gpt-oss-20b"
    llm_primary_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_fallback_base_url: str = "https://api.groq.com/openai/v1"
    llm_timeout_seconds: float = 30.0
    usd_inr: float = 95.0
    prompts_dir: Path = Path("prompts")
    # Queue and worker (Day 10).
    redis_url: str = "redis://localhost:6379"
    manifest_file: Path = Path("data/manifest.jsonl")
    admin_token: str = ""
    worker_in_api: bool = False
    ingest_concurrency: int = 2
    ingest_rpm: float = 12.0
    ingest_job_timeout: int = 60
    ingest_max_tries: int = 3


@lru_cache
def get_settings() -> Settings:
    """Build the settings once and reuse them."""
    return Settings()
