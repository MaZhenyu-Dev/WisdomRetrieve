from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.mysql import get_db_session
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentIndexData,
    DocumentResponse,
    DocumentUploadData,
)
from app.schemas.response import ApiResponse, PageData, success_response
from app.service.document_service import (
    delete_document,
    get_document_or_404,
    list_document_chunks,
    list_documents,
    rebuild_document_index,
    retry_parse_document,
    upload_pdf_document,
)

router = APIRouter(prefix="/api/document", tags=["document"])


@router.post("/upload", response_model=ApiResponse[DocumentUploadData])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
) -> ApiResponse[DocumentUploadData]:
    document = await upload_pdf_document(db, file)
    return success_response(
        DocumentUploadData(
            file_id=document.id,
            status=document.parse_status,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
        )
    )


@router.get("", response_model=ApiResponse[PageData[DocumentResponse]])
@router.get("/", response_model=ApiResponse[PageData[DocumentResponse]])
@router.get("/list", response_model=ApiResponse[PageData[DocumentResponse]])
def get_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=255),
    parse_status: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db_session),
) -> ApiResponse[PageData[DocumentResponse]]:
    total, documents = list_documents(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        parse_status=parse_status,
    )
    return success_response(
        PageData(
            items=[DocumentResponse.model_validate(document) for document in documents],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/{document_id}/file")
def preview_document_file(
    document_id: int,
    db: Session = Depends(get_db_session),
) -> FileResponse:
    document = get_document_or_404(db, document_id)
    file_path = Path(document.file_path)
    if not file_path.exists() or not file_path.is_file():
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found.",
        )
    return FileResponse(
        path=file_path,
        media_type=document.mime_type or "application/pdf",
        filename=document.file_name,
        content_disposition_type="inline",
    )


@router.get("/{document_id}/chunks", response_model=ApiResponse[PageData[DocumentChunkResponse]])
def get_document_chunks(
    document_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> ApiResponse[PageData[DocumentChunkResponse]]:
    total, chunks = list_document_chunks(db, document_id, page=page, page_size=page_size)
    return success_response(
        PageData(
            items=[DocumentChunkResponse.model_validate(chunk) for chunk in chunks],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/{document_id}/retry", response_model=ApiResponse[DocumentResponse])
def retry_document_parse(
    document_id: int,
    db: Session = Depends(get_db_session),
) -> ApiResponse[DocumentResponse]:
    document = retry_parse_document(db, document_id)
    return success_response(DocumentResponse.model_validate(document))


@router.post("/index", response_model=ApiResponse[DocumentIndexData])
def rebuild_index(
    db: Session = Depends(get_db_session),
) -> ApiResponse[DocumentIndexData]:
    chunk_count, version = rebuild_document_index(db)
    return success_response(
        DocumentIndexData(
            chunk_count=chunk_count,
            knowledge_base_version=version,
        )
    )


@router.delete("/{document_id}", response_model=ApiResponse[None])
def remove_document(
    document_id: int,
    db: Session = Depends(get_db_session),
) -> ApiResponse[None]:
    delete_document(db, document_id)
    return success_response(None)
