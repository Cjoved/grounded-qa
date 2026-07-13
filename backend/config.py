"""Environment configuration.

Loads from `.env` in local dev via python-dotenv. In production (Render),
these are set directly in the service's environment variable settings.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# AI provider (OpenRouter, NVIDIA NIM, or anything OpenAI-compatible)
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://openrouter.ai/api/v1")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_MODEL = os.environ.get("AI_MODEL", "openrouter/free")

# Embeddings (FastEmbed local ONNX, no GPU, no API cost)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# Qdrant
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_COLLECTION = "documents"

# Supabase Auth
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
ALLOWED_EMAIL = os.environ.get("ALLOWED_EMAIL", "")

# LangSmith (tracing for the /ask graph, evaluation backbone for eval_harness)
#
# NOTE: the `langsmith` SDK reads LANGSMITH_TRACING / LANGSMITH_API_KEY /
# LANGSMITH_ENDPOINT / LANGSMITH_PROJECT directly from os.environ itself
# (that's how @traceable, wrap_openai(), and Client() auto-configure) — so
# this is the one exception to "never read os.environ directly outside
# config.py". We still mirror the values here so the rest of the app has a
# single place to check whether tracing is on (e.g. to log a startup
# warning) without re-parsing env vars.
LANGSMITH_TRACING = os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.environ.get("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.environ.get("LANGSMITH_PROJECT", "grounded-qa")
LANGSMITH_ENDPOINT = os.environ.get(
    "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
)
