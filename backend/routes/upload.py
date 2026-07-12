"""Upload endpoint — see BLUEPRINT.md section 10 for the full contract.

Week 1 task: wire this up to services/ingestion.py (Docling parse -> chunk
-> FastEmbed -> Qdrant store).
"""

from fastapi import APIRouter, UploadFile

from schemas import DocumentListResponse, UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile):
    # TODO (Week 1): call services.ingestion.ingest_file(file)
    raise NotImplementedError("Wire this up to services/ingestion.py")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    # TODO (Week 1): query Qdrant for distinct document_ids + metadata
    raise NotImplementedError("Wire this up to services/ingestion.py")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    # TODO (Week 1/2): delete all chunks for this document_id from Qdrant
    raise NotImplementedError("Wire this up to services/ingestion.py")
