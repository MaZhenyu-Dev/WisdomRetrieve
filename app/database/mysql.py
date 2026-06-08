from collections.abc import Generator
from functools import lru_cache
import re

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import Base


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.mysql_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )


def get_server_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        (
            "mysql+pymysql://"
            f"{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/"
            "?charset=utf8mb4"
        ),
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_mysql_tables() -> None:
    ensure_database_exists()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    ensure_qa_log_columns(engine)
    ensure_chat_history_columns(engine)


def ensure_qa_log_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "qa_logs" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("qa_logs")}
    column_sql = {
        "cache_hit": "ALTER TABLE qa_logs ADD COLUMN cache_hit BOOL NOT NULL DEFAULT FALSE",
        "question_hash": "ALTER TABLE qa_logs ADD COLUMN question_hash VARCHAR(64) NULL",
        "knowledge_base_version": (
            "ALTER TABLE qa_logs ADD COLUMN knowledge_base_version VARCHAR(64) NULL"
        ),
        "document_ids": "ALTER TABLE qa_logs ADD COLUMN document_ids TEXT NULL",
    }
    with engine.begin() as connection:
        for column_name, statement in column_sql.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def ensure_chat_history_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "chat_history" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("chat_history")}
    column_sql = {
        "sources": "ALTER TABLE chat_history ADD COLUMN sources TEXT NULL",
    }
    with engine.begin() as connection:
        for column_name, statement in column_sql.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def ensure_database_exists() -> None:
    settings = get_settings()
    database_name = settings.mysql_database
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise ValueError("MYSQL_DATABASE may only contain letters, numbers, and underscores.")

    with get_server_engine().begin() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )


def ping_mysql() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
        return True
    except Exception:
        return False
