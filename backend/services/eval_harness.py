"""Eval harness: retrieval hit-rate, faithfulness, and relevance scoring.

Backbone: LangSmith's dataset + `Client.evaluate()`, instead of a hand-rolled
loop over EVAL_QUESTIONS. This is the main place LangSmith earns its spot in
the stack (see BLUEPRINT.md section 2): a dataset of eval questions lives in
LangSmith (versioned, editable from the UI or the SDK), `run_eval()` runs the
real /ask graph (graphs/ask_graph.py) against every example, and each metric
below is registered as a LangSmith evaluator. LangSmith records the full
experiment (every run + every score); we then reshape that into the existing
EvalResult / EvalRunResponse Pydantic contract so `routes/eval.py` and the
Vue EvalDashboard.vue component don't have to change at all.

See .claude/skills/eval-metric-conventions/SKILL.md before adding a new
metric. See BLUEPRINT.md section 6 for the eval question set format and
section 10 for the response shape.
"""

import uuid

from langsmith import Client, traceable

from graphs.ask_graph import run_ask
from schemas import EvalResult, EvalRunResponse, EvalSummary

DATASET_NAME = "grounded-qa-eval-set"

# TODO (Week 3): replace with a real eval set of 10-20 questions, each with
# an expected_source and (ideally) an expected_answer to compare against.
# This local list is the source of truth that gets synced into the LangSmith
# dataset by _ensure_dataset() below — edit here, not in the LangSmith UI,
# so the eval set stays version-controlled with the rest of the repo.
EVAL_QUESTIONS: list[dict] = []


def _ensure_dataset(client: Client) -> str:
    """Create the LangSmith dataset on first run and keep it in sync with
    EVAL_QUESTIONS. Returns the dataset name (client.evaluate() accepts a
    name directly, no need to resolve to an ID).

    TODO (Week 3): decide the sync strategy once EVAL_QUESTIONS is non-empty
    — the simplest correct approach is "diff by question text, add missing
    examples, leave existing ones alone" rather than wiping and recreating
    the dataset on every run (that would lose LangSmith-side run history).
    """
    if not client.has_dataset(dataset_name=DATASET_NAME):
        client.create_dataset(dataset_name=DATASET_NAME)
    # TODO: client.create_examples(...) for any EVAL_QUESTIONS entries not
    # already present (compare against client.list_examples(dataset_name=...)).
    return DATASET_NAME


@traceable(name="eval_target", run_type="chain")
def _target(inputs: dict) -> dict:
    """The function LangSmith runs once per dataset example. Deliberately
    calls the *real* ask_graph (not a reimplementation) so eval results
    reflect the actual /ask pipeline, per the module docstring above.
    """
    state = run_ask(inputs["question"])
    return {
        "answer": state["answer"],
        "sources": [s.model_dump() for s in state["sources"]],
    }


def score_retrieval_hit(expected_source: str, retrieved_sources: list[str]) -> bool:
    """Deterministic check: did the expected source appear in top-k results?"""
    return expected_source in retrieved_sources


def retrieval_hit_evaluator(run, example) -> dict:
    """LangSmith evaluator wrapping score_retrieval_hit. `run.outputs` is
    whatever `_target()` returned; `example.outputs` is the reference data
    attached to the dataset example (expected_source).
    """
    retrieved = [s["filename"] for s in run.outputs.get("sources", [])]
    expected = example.outputs.get("expected_source", "")
    return {
        "key": "retrieval_hit",
        "score": score_retrieval_hit(expected, retrieved),
    }


@traceable(name="score_faithfulness", run_type="llm")
def score_faithfulness(context: str, answer: str) -> float:
    """LLM-as-judge: is the answer fully supported by the context?

    TODO (Week 3): use a DIFFERENT model/provider than the one used for
    generation (see BLUEPRINT.md section 14 risk table — a model grading its
    own output is a biased judge), prompt it to respond with only a number
    from 0 to 1.
    """
    raise NotImplementedError


def faithfulness_evaluator(run, example) -> dict:
    context = "\n".join(s["chunk_text"] for s in run.outputs.get("sources", []))
    score = score_faithfulness(context, run.outputs.get("answer", ""))
    return {"key": "faithfulness", "score": score}


@traceable(name="score_relevance", run_type="llm")
def score_relevance(question: str, answer: str) -> float:
    """LLM-as-judge: does the answer actually address the question?

    TODO (Week 3): same judge-model considerations as score_faithfulness.
    """
    raise NotImplementedError


def relevance_evaluator(run, example) -> dict:
    score = score_relevance(example.inputs.get("question", ""), run.outputs.get("answer", ""))
    return {"key": "relevance", "score": score}


def run_eval() -> EvalRunResponse:
    """Run the full eval set through LangSmith and return per-question
    results + summary, reshaped into the existing API contract.

    TODO (Week 3): this is wired up structurally but will raise
    NotImplementedError as soon as it hits run_ask() -> retrieval.search() /
    generation.generate_answer(), same as everything else in the scaffold —
    it becomes runnable once Week 1/2 services are implemented.
    """
    client = Client()
    dataset_name = _ensure_dataset(client)

    experiment_results = client.evaluate(
        _target,
        data=dataset_name,
        evaluators=[retrieval_hit_evaluator, faithfulness_evaluator, relevance_evaluator],
        experiment_prefix="grounded-qa-ask",
    )

    results: list[EvalResult] = []
    for row in experiment_results:
        scores = {r.key: r.score for r in row["evaluation_results"]["results"]}
        results.append(
            EvalResult(
                question=row["example"].inputs.get("question", ""),
                expected_source=row["example"].outputs.get("expected_source"),
                retrieval_hit=bool(scores.get("retrieval_hit", False)),
                faithfulness_score=float(scores.get("faithfulness", 0.0)),
                relevance_score=float(scores.get("relevance", 0.0)),
            )
        )

    summary = _summarize(results)
    # experiment_results carries a LangSmith experiment/session id — surface
    # it as run_id so a person can jump from the Vue dashboard straight to
    # the matching LangSmith experiment if they want the full trace detail.
    run_id = getattr(experiment_results, "experiment_name", str(uuid.uuid4()))
    return EvalRunResponse(run_id=run_id, results=results, summary=summary)


def _summarize(results: list[EvalResult]) -> EvalSummary:
    if not results:
        return EvalSummary(avg_retrieval_hit_rate=0.0, avg_faithfulness=0.0, avg_relevance=0.0)
    n = len(results)
    return EvalSummary(
        avg_retrieval_hit_rate=sum(r.retrieval_hit for r in results) / n,
        avg_faithfulness=sum(r.faithfulness_score for r in results) / n,
        avg_relevance=sum(r.relevance_score for r in results) / n,
    )
