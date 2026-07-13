"""Qdrant client singleton + upsert/search helpers."""

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FilterSelector,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)
from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Return singleton Qdrant client."""
    global _client
    if _client is None:
        if not QDRANT_URL or not QDRANT_API_KEY:
            raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set in environment")
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        _ensure_collection(_client)
    return _client


def _ensure_collection(client: QdrantClient) -> None:
    """Create collection if missing, and ensure payload indexes for filtered ops."""
    collections = client.get_collections().collections
    if not any(c.name == QDRANT_COLLECTION for c in collections):
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    _ensure_payload_indexes(client)


def _ensure_payload_indexes(client: QdrantClient) -> None:
    """Qdrant Cloud requires a keyword index before filtering on document_id."""
    info = client.get_collection(QDRANT_COLLECTION)
    schema = info.payload_schema or {}
    if "document_id" not in schema:
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )


def upsert_chunks(document_id: str, filename: str, chunks: list[str], vectors: list[list[float]]) -> int:
    """Upsert chunk vectors + payload into Qdrant. Returns count upserted."""
    client = get_qdrant_client()
    points = [
        PointStruct(
            id=hash(f"{document_id}_{i}") % (2**63),
            vector=vector,
            payload={
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "text": chunk,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


def search_chunks(query_vector: list[float], top_k: int = 5) -> list[dict]:
    """Search chunks by vector similarity. Returns list of payload dicts with score."""
    client = get_qdrant_client()
    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {"score": r.score, **r.payload}
        for r in results
    ]


def get_documents() -> list[dict]:
    """List all unique documents (by document_id) with chunk counts."""
    client = get_qdrant_client()
    # Scroll through all points to group by document_id
    points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )
    doc_map: dict[str, dict] = {}
    for p in points:
        did = p.payload["document_id"]
        if did not in doc_map:
            doc_map[did] = {
                "document_id": did,
                "filename": p.payload["filename"],
                "chunk_count": 0,
            }
        doc_map[did]["chunk_count"] += 1
    return list(doc_map.values())


def delete_document(document_id: str) -> int:
    """Delete all chunks for a document. Returns count deleted."""
    client = get_qdrant_client()
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )
        ),
        wait=True,
    )
    return 1