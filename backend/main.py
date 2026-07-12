import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import LANGSMITH_API_KEY, LANGSMITH_PROJECT, LANGSMITH_TRACING
from routes.ask import router as ask_router
from routes.eval import router as eval_router
from routes.upload import router as upload_router

logger = logging.getLogger("grounded_qa")

app = FastAPI(title="Grounded Q&A API")

if LANGSMITH_TRACING and not LANGSMITH_API_KEY:
    logger.warning(
        "LANGSMITH_TRACING=true pero walang LANGSMITH_API_KEY — the /ask "
        "graph and eval harness will run without tracing/eval upload."
    )
elif LANGSMITH_TRACING:
    logger.info("LangSmith tracing enabled (project=%s)", LANGSMITH_PROJECT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to your actual frontend domain before going public
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(eval_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
