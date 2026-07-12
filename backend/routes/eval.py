"""Eval endpoints — see BLUEPRINT.md sections 6, 10, 12 for the eval set
format, API contract, and metric conventions.

Week 3 task: wire this up to services/eval_harness.py.
"""

from fastapi import APIRouter

from schemas import EvalRunResponse

router = APIRouter()


@router.post("/eval/run", response_model=EvalRunResponse)
async def run_eval():
    from services.eval_harness import run_eval as run_eval_service

    return run_eval_service()


@router.get("/eval/history")
async def eval_history():
    # TODO (Week 3): past runs now live in LangSmith as experiments against
    # the "grounded-qa-eval-set" dataset (services/eval_harness.py
    # DATASET_NAME), not in our own DB — list them with
    # `langsmith.Client().list_projects(reference_dataset_name=DATASET_NAME)`
    # (confirm the exact SDK call against current LangSmith docs when you
    # implement this — the SDK surface moves fast), then reshape each
    # experiment's summary scores into the same shape run_eval() returns so
    # EvalDashboard.vue's history view doesn't need special-casing.
    raise NotImplementedError("Wire this up to services/eval_harness.py")
