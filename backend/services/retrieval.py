"""Retrieval: embed a query and search Qdrant for the top-k relevant chunks.

See BLUEPRINT.md section 11 for the Qdrant collection schema.
"""

from langsmith import traceable

from schemas import SourceChunk


@traceable(name="retrieve_chunks", run_type="retriever")
def search(question: str, top_k: int = 5) -> list[SourceChunk]:
    """Embed `question` and return the top_k most relevant chunks from Qdrant.

    TODO (Week 2): use the qdrant-client FastEmbed integration to embed the
    query and run a similarity search against the `documents` collection.
    run_type="retriever" makes this render as a retrieval step (not a plain
    function call) in the LangSmith trace tree for the /ask graph.
    """
    raise NotImplementedError
