"""FastEmbed singleton — local ONNX embeddings, no GPU, no external API."""

from fastembed import TextEmbedding
from config import EMBEDDING_MODEL


_embedding_model: TextEmbedding | None = None


def get_embedding_model() -> TextEmbedding:
    """Lazy singleton: loads FastEmbed model on first call."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returning list of vector lists [batch, dim]."""
    model = get_embedding_model()
    return [embedding.tolist() for embedding in model.embed(texts)]