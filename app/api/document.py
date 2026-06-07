from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.database.mysql import get_db_session
from app.schemas.document import (
    DocumentIndexData,
    DocumentResponse,
    DocumentUploadData,
)
from app.schemas.response import ApiResponse, PageData, success_response
from app.service.document_service import (
    delete_document,
    list_documents,
    rebuild_document_index,
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
    db: Session = Depends(get_db_session),
) -> ApiResponse[PageData[DocumentResponse]]:
    total, documents = list_documents(db, page=page, page_size=page_size)
    return success_response(
        PageData(
            items=[DocumentResponse.model_validate(document) for document in documents],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


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
