from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "WisdomRetrieve"
    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = Field(default="040716", repr=False)
    mysql_database: str = "wisdom_retrieve"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = Field(default=None, repr=False)

    dashscope_api_key: str | None = Field(default=None, repr=False)
    dashscope_embedding_model: str = "text-embedding-v1"
    # qwen_api_key: str | None = Field(default=None, repr=False)
    qwen_model: str = "qwen3.7-plus"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_rerank_model: str = "qwen3-rerank"
    qwen_rerank_base_url: str = "https://dashscope.aliyuncs.com/compatible-api/v1"

    rag_context_max_chars: int = 6000
    qa_cache_ttl_seconds: int = 24 * 60 * 60

    chromadb_path: Path = Path("./chroma_db")
    upload_dir: Path = Path("./uploads")

    @property
    def mysql_url(self) -> str:
        return (
            "mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
