---
name: adding-ingestion-format
description: Use this skill when the user asks to add support for a new file type/format in the ingestion pipeline, or when a file fails to parse correctly and needs special handling beyond what Docling provides by default.
---

# Adding a New Ingestion Format

Docling already handles PDF, DOCX, PPTX, HTML, Markdown, AsciiDoc, and common
image formats through a single unified API — for most new file types, **no
new code is needed**, only a check that Docling supports it.

## Steps

1. Confirm the format isn't already covered by Docling's `DocumentConverter`.
   If it is, no changes are needed — the existing `services/ingestion.py`
   pipeline already handles it.
2. If it's genuinely unsupported (e.g. a proprietary format, a plain-text
   format Docling doesn't target, or a format needing custom pre-processing):
   - Add a dedicated parsing function in `backend/services/ingestion.py`
   - Keep the function's output shape identical to Docling's output
     (Markdown text) so the rest of the pipeline — chunking, embedding,
     storage — doesn't need to branch on file type
   - Route to it based on file extension in the same ingestion entrypoint,
     keep the dispatch logic in one place
3. Test with a real sample file before considering it done — confirm
   chunk count and chunk content look reasonable, not just that it doesn't
   error

## Don't

- Don't scatter format-specific logic across multiple files — the ingestion
  entrypoint should be the single place that decides how to parse a file
- Don't change the chunk/embedding/storage steps to accommodate a new
  format — if a new format's output can't be normalized to Markdown text,
  reconsider whether it belongs in this pipeline at all
