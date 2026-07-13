"""Document routes: GET /documents, DELETE /documents/{id}."""

from fastapi import APIRouter, Depends
from services.qdrant import get_documents, delete_document
from services.auth import require_auth


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(require_auth)])


@router.get("")
async def list_documents():
    """List all uploaded documents with chunk counts."""
    return get_documents()


@router.delete("/{document_id}")
async def delete_document_route(document_id: str):
    """Delete a document and all its chunks from the vector store."""
    delete_document(document_id)
    return {"deleted": True, "document_id": document_id}
