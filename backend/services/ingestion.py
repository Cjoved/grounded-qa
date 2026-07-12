"""Ingestion pipeline: file -> Docling -> chunks -> FastEmbed -> Qdrant.

See BLUEPRINT.md section 12 for the proposed chunking strategy and section 11
for the Qdrant payload schema. See
.claude/skills/adding-ingestion-format/SKILL.md before adding format-specific
logic here — Docling should cover most file types without it.
"""

from docling.document_converter import DocumentConverter


def parse_document(file_path: str) -> str:
    """Convert any supported file to Markdown text via Docling."""
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


def chunk_markdown(markdown_text: str) -> list[str]:
    """Heading-aware chunking with fixed-size fallback.

    TODO (Week 1): implement per BLUEPRINT.md section 12 —
      1. split on markdown headings
      2. split sections over ~500 tokens into 300-400 token chunks with
         ~50 token overlap
      3. merge sections under ~50 tokens into the neighboring section
    """
    raise NotImplementedError


def embed_and_store(document_id: str, filename: str, chunks: list[str]) -> int:
    """Embed chunks with FastEmbed and upsert them into Qdrant.

    TODO (Week 1): use qdrant_client's built-in FastEmbed integration
    (`qdrant-client[fastembed]`) to embed + upsert in one step. Returns the
    number of chunks stored.
    """
    raise NotImplementedError


def ingest_file(file_path: str, filename: str) -> dict:
    """Full pipeline entrypoint used by routes/upload.py."""
    markdown_text = parse_document(file_path)
    chunks = chunk_markdown(markdown_text)
    chunks_created = embed_and_store(document_id="", filename=filename, chunks=chunks)
    return {"chunks_created": chunks_created}
