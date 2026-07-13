"""Ingestion pipeline: file -> Docling -> chunks -> FastEmbed -> Qdrant.

See BLUEPRINT.md section 12 for the proposed chunking strategy and section 11
for the Qdrant payload schema. See
.claude/skills/adding-ingestion-format/SKILL.md before adding format-specific
logic here — Docling should cover most file types without it.
"""

import hashlib
import re
from typing import List

from docling.document_converter import DocumentConverter

from services.embedding import embed_texts
from services.qdrant import upsert_chunks


def parse_document(file_path: str) -> str:
    """Convert any supported file to Markdown text via Docling."""
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


def chunk_markdown(markdown_text: str) -> List[str]:
    """Heading-aware chunking with fixed-size fallback.

    Strategy (per BLUEPRINT.md section 12):
      1. Split on markdown headings (# ## ###)
      2. Split sections over ~500 tokens into 300-400 token chunks with ~50 token overlap
      3. Merge sections under ~50 tokens into the neighboring section

    Approximate token count: ~1.3 tokens per word for English.
    Target chunk ~350 tokens ~= ~270 words ~= ~1500 chars.
    """
    # Step 1: split on headings
    heading_pattern = r"^(#{1,6}\s+.+)$"
    parts = re.split(heading_pattern, markdown_text, flags=re.MULTILINE)

    # Reconstruct sections with their headings
    sections: List[str] = []
    current_section = ""

    for i, part in enumerate(parts):
        if re.match(heading_pattern, part, flags=re.MULTILINE):
            # This is a heading
            if current_section.strip():
                sections.append(current_section.strip())
            current_section = part + "\n"
        else:
            current_section += part

    if current_section.strip():
        sections.append(current_section.strip())

    # If no headings found, treat whole doc as one section
    if not sections:
        sections = [markdown_text]

    # Step 2 & 3: chunk large sections, merge tiny ones
    final_chunks: List[str] = []
    target_chars = 1500  # ~350 tokens
    overlap_chars = 200  # ~50 tokens
    min_chars = 220      # ~50 tokens

    for section in sections:
        if len(section) <= target_chars:
            # Small enough — check if we should merge with previous
            if final_chunks and len(section) < min_chars:
                final_chunks[-1] += "\n\n" + section
            else:
                final_chunks.append(section)
        else:
            # Large section — split into overlapping chunks
            words = section.split()
            chunk_words: List[str] = []
            char_count = 0

            for word in words:
                chunk_words.append(word)
                char_count += len(word) + 1

                if char_count >= target_chars:
                    chunk_text = " ".join(chunk_words)
                    final_chunks.append(chunk_text)

                    # Keep overlap words for next chunk
                    overlap_words_count = max(1, len(chunk_words) * overlap_chars // target_chars)
                    chunk_words = chunk_words[-overlap_words_count:]
                    char_count = sum(len(w) + 1 for w in chunk_words)

            # Remainder
            if chunk_words:
                remainder = " ".join(chunk_words)
                if final_chunks and len(remainder) < min_chars:
                    final_chunks[-1] += "\n\n" + remainder
                else:
                    final_chunks.append(remainder)

    # Filter empty
    return [c.strip() for c in final_chunks if c.strip()]


def _compute_doc_id(filename: str, chunks: List[str]) -> str:
    """Deterministic document ID from filename + content hash."""
    content_hash = hashlib.md5("".join(chunks).encode()).hexdigest()[:12]
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", filename)[:50]
    return f"{safe_name}_{content_hash}"


def ingest_file(file_bytes: bytes, filename: str) -> dict:
    """Full pipeline entrypoint used by routes/upload.py."""
    import tempfile
    import os

    # Write bytes to temp file for Docling
    suffix = os.path.splitext(filename)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        markdown_text = parse_document(tmp_path)
        chunks = chunk_markdown(markdown_text)

        if not chunks:
            return {"chunks_created": 0, "document_id": ""}

        document_id = _compute_doc_id(filename, chunks)
        vectors = embed_texts(chunks)
        chunks_created = upsert_chunks(document_id, filename, chunks, vectors)

        return {"chunks_created": chunks_created, "document_id": document_id}
    finally:
        os.unlink(tmp_path)