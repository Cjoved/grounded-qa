"""Upload route: POST /upload."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from services.ingestion import ingest_file
from services.auth import require_auth


router = APIRouter(prefix="/upload", tags=["upload"], dependencies=[Depends(require_auth)])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document (PDF, DOCX, PPTX, etc.) and ingest into vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_ext = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html", ".htm"}
    if not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_ext)}")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")

    result = ingest_file(content, file.filename)
    return {
        **result,
        "filename": file.filename,
        "status": "indexed" if result.get("chunks_created", 0) > 0 else "empty",
    }
