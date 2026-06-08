from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.cache.redis import refresh_knowledge_base_version
from app.config import get_settings
from app.database.models import Document, DocumentChunk
from app.parser.pdf import parse_pdf
from app.retrieval.chroma_store import add_document_chunks, delete_document_chunks, rebuild_document_chunks
from app.splitter.text import split_pages

PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


async def upload_pdf_document(db: Session, file: UploadFile) -> Document:
    file_name = Path(file.filename or "").name
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing upload file name.",
        )
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )
    if file.content_type and file.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF is empty.",
        )

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_file_name = f"{uuid.uuid4().hex}.pdf"
    file_path = upload_dir / stored_file_name
    file_path.write_bytes(content)

    document = Document(
        file_name=file_name,
        stored_file_name=stored_file_name,
        file_path=str(file_path),
        file_size=len(content),
        file_sha256=hashlib.sha256(content).hexdigest(),
        mime_type=file.content_type or "application/pdf",
        parse_status="parsing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        return _parse_and_index_document(db, document, file_path)
    except HTTPException:
        raise
    except Exception as exc:
        _mark_parse_failed(db, document.id, exc)


def list_documents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    parse_status: str | None = None,
) -> tuple[int, list[Document]]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    filters = []
    if keyword:
        filters.append(Document.file_name.like(f"%{keyword.strip()}%"))
    if parse_status:
        filters.append(Document.parse_status == parse_status)

    total_query = select(func.count()).select_from(Document)
    query = select(Document)
    if filters:
        total_query = total_query.where(*filters)
        query = query.where(*filters)

    total = db.scalar(total_query) or 0
    documents = list(
        db.scalars(
            query
            .order_by(Document.created_at.desc(), Document.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return total, documents


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return document


def list_document_chunks(
    db: Session,
    document_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[DocumentChunk]]:
    get_document_or_404(db, document_id)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = (
        db.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
        or 0
    )
    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc(), DocumentChunk.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return total, chunks


def retry_parse_document(db: Session, document_id: int) -> Document:
    document = get_document_or_404(db, document_id)
    file_path = Path(document.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found.",
        )

    document.parse_status = "parsing"
    document.error_message = None
    db.commit()
    db.refresh(document)

    try:
        return _parse_and_index_document(db, document, file_path, replace_existing=True)
    except Exception as exc:
        _mark_parse_failed(db, document.id, exc)


def delete_document(db: Session, document_id: int) -> int:
    document = get_document_or_404(db, document_id)

    file_path = Path(document.file_path)
    delete_document_chunks(document_id)
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    db.delete(document)
    db.commit()

    _delete_file(file_path)
    refresh_knowledge_base_version()
    return document_id


def rebuild_document_index(db: Session) -> tuple[int, str | None]:
    chunks = list(
        db.scalars(
            select(DocumentChunk).order_by(
                DocumentChunk.document_id.asc(),
                DocumentChunk.chunk_index.asc(),
            )
        )
    )
    rebuild_document_chunks(chunks)
    version = refresh_knowledge_base_version()
    return len(chunks), version


def _parse_and_index_document(
    db: Session,
    document: Document,
    file_path: Path,
    replace_existing: bool = False,
) -> Document:
    parsed_pdf = parse_pdf(file_path)
    text_chunks = split_pages(parsed_pdf.pages)
    chunk_rows = [
        DocumentChunk(
            document_id=document.id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            file_name=document.file_name,
            title=chunk.title,
            content=chunk.content,
            chroma_id=f"doc:{document.id}:chunk:{chunk.chunk_index}",
        )
        for chunk in text_chunks
    ]

    if replace_existing:
        delete_document_chunks(document.id)
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        db.flush()

    db.add_all(chunk_rows)
    add_document_chunks(chunk_rows)

    document.page_count = parsed_pdf.page_count
    document.chunk_count = len(chunk_rows)
    document.parse_status = "parsed"
    document.error_message = None
    db.commit()
    refresh_knowledge_base_version()
    db.refresh(document)
    return document


def _mark_parse_failed(db: Session, document_id: int, exc: Exception) -> None:
    db.rollback()
    _cleanup_failed_chroma(document_id)
    document = db.get(Document, document_id)
    if document is not None:
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        document.page_count = 0
        document.chunk_count = 0
        document.parse_status = "failed"
        document.error_message = str(exc)[:2000]
        db.commit()
        db.refresh(document)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "message": "PDF parsing failed.",
            "file_id": document_id,
            "error": str(exc)[:2000],
        },
    ) from exc


def _delete_file(file_path: Path) -> None:
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except OSError:
        pass


def _cleanup_failed_chroma(document_id: int) -> None:
    try:
        delete_document_chunks(document_id)
    except Exception:
        pass
