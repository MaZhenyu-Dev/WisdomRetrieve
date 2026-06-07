from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_size: int
    parse_status: str
    page_count: int
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentUploadData(BaseModel):
    file_id: int
    status: str
    page_count: int
    chunk_count: int


class DocumentIndexData(BaseModel):
    chunk_count: int
    knowledge_base_version: str | None = None
