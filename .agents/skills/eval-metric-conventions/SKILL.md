---
name: eval-metric-conventions
description: Use this skill when the user asks to add a new evaluation metric to the eval harness, modify how existing metrics (retrieval hit-rate, faithfulness, relevance) are scored, or extend the eval question set.
---

# Eval Metric Conventions

The eval harness lives in `backend/services/eval_harness.py` and is driven by
a fixed set of eval questions (see `BLUEPRINT.md` section 6 for the current
question set format). Each metric is a self-contained scoring function so new
metrics can be added without touching existing ones.

## Existing metrics

- **Retrieval hit-rate** — did the expected source document/chunk appear in
  the top-k retrieved results? Deterministic, no LLM call needed.
- **Faithfulness** — LLM-as-judge: given the retrieved context and the
  generated answer, does the answer only state things supported by the
  context? Use a different model/provider than the one used for generation,
  to avoid a model grading its own output.
- **Relevance** — LLM-as-judge: does the answer actually address the
  question asked, independent of whether it's grounded?

## Adding a new metric

1. Write a function in `eval_harness.py` with the signature
   `(question, retrieved_chunks, generated_answer) -> float` (0.0–1.0 scale,
   consistent with the existing metrics)
2. Register it in the metrics list that `run_eval()` iterates over — don't
   hardcode a new metric into the main eval loop itself
3. Update the `/eval/run` response schema in `schemas.py` to include the new
   score
4. Update the Vue `EvalDashboard.vue` component to display it

## Rules

- Keep LLM-as-judge prompts short and specific about the output format
  (e.g. "respond with only a number from 0 to 1") — don't ask for free-form
  explanations unless the UI is also updated to show them
- Every metric must return a numeric score — no metric should silently fail;
  if scoring can't complete for a question, record it as `null` and surface
  that in the dashboard rather than skipping the question
- When adding or changing the eval question set, keep questions answerable
  strictly from the uploaded documents — a question the documents can't
  actually answer makes every metric meaningless for that row
