- Date: 2026-10-05
- Task / purpose: Implement the GPT-5.4 oracle-context generation calibration
- Git branch: work
- Related PR: unknown
- Commit SHA: bcf88e2 (pre-task source revision)
- Output status: Raw/verbatim (repository-relative paths used; no secrets present)

---

### Summary

* Added the fixed, versioned ten-question calibration set: Q001, Q002, Q007, Q008, Q014, Q017, Q022, Q034, Q038, and Q040. The rationales deliberately cover a basic definition, duration and numerical rules, waiting-period interactions, exceptions and overrides, multi-fact/multi-location evidence, cross-page and MediCare Plus representation difficulty, and the required Q040 negative-space protocol. 【F:configs/oracle_generation_calibration_v1.json†L20-L36】
* Froze the experiment to the `oracle_context` arm with OpenAI `gpt-5.4`, `low` reasoning, default/standard service, prompt `oracle-policy-qa-v1`, answer schema `generation-answer-v1`, and evaluator `generation-v1`. Versioned standard pricing is $2.50/M uncached input, $0.25/M cached input, and $15/M output; calculated cost is explicitly an estimate rather than an invoice. 【F:configs/oracle_generation_calibration_v1.json†L2-L19】
* Added a policy-neutral, reusable prompt that limits answers to supplied evidence, preserves conditions/exceptions/overrides, requires insufficiency rather than unsupported inference, atomizes factual claims, and cites only supplied context identifiers. 【F:prompts/oracle_policy_qa_v1.txt†L1-L18】
* Added a minimal structured-output schema for the answer, atomic factual claims, claim-associated context citations, and the insufficient-evidence indicator; it contains no model self-scoring fields. 【F:evals/generation_answer_v1.schema.json†L1-L31】
* Implemented deterministic context construction directly from Evaluation Contract v2 fragments. Every required positive evidence unit is checked before client creation; Q040 instead receives only its reviewed nearby clauses, clearly marked as non-positive evidence. Stable context IDs plus exact source, page, unit, role, and text provenance are persisted with the rendered prompt. 【F:src/evaluation/oracle_generation_calibration.py†L43-L94】【F:src/evaluation/oracle_generation_calibration.py†L221-L235】
* Implemented a reproducible Responses API harness with no tools, strict structured output, environment-only API-key handling, zero-call dry-run mode, raw provider-response persistence, normalized records, API/parse error recording without fabricated answers, usage/cached-token cost calculation, aggregate latency and token accounting, and hard run-directory collision protection. The configuration cap prevents accidentally selecting the full benchmark. 【F:src/evaluation/oracle_generation_calibration.py†L29-L41】【F:src/evaluation/oracle_generation_calibration.py†L203-L300】
* Added a compact human-review worksheet. It carries unchanged questions, expected answers and required facts, exact supplied evidence/provenance, generated claims/citations, and blank Contract v1 label fields. Semantic correctness labels are deliberately not fabricated. 【F:src/evaluation/oracle_generation_calibration.py†L170-L198】
* Added deterministic coverage for selection, context completeness, prompt construction, parsing and citation resolution, zero-call dry runs, missing-key safety, cost math, failed calls, collision protection, and Q040 handling. 【F:tests/test_oracle_generation_calibration.py†L25-L161】
* Documented construction, output layout, claim-atomization guidance, pricing, acceptance gates, the exact local live command, assumptions, and limitations. The timelapse separately records implementation, dry-run, blocked live status, controls, selection, usage/cost/latency, failures, and human-review status. 【F:docs/oracle_generation_calibration_v1.md†L1-L128】【F:docs/timelapse.md†L507-L551】

### Experiment status and outputs

* The dry run validated all ten questions and wrote its reproducibility artifact to `artifacts/generation/oracle_calibration/20261005T000000Z_dry_run_v1/`. It made **0 API calls**, used **0 tokens**, incurred **$0 estimated API cost**, and has no latency measurement because no request was made. 【F:artifacts/generation/oracle_calibration/20261005T000000Z_dry_run_v1/run_manifest.json†L1-L46】
* The live experiment did **not** occur: `OPENAI_API_KEY` is absent in this environment. Live status is **BLOCKED**, not failed or measured. No generated answer, generation metric, human label, or quality conclusion was fabricated.
* The generated-answer review template is at `artifacts/generation/oracle_calibration/20261005T000000Z_dry_run_v1/human_review.md`; after a live run, the equivalent file in the unique live-run directory will contain actual answers and remain blank for human semantic labels. 【F:artifacts/generation/oracle_calibration/20261005T000000Z_dry_run_v1/human_review.md†L1-L18】
* Assumption: authoritative v2 fragment text is the oracle prompt evidence, while Q040's gold spans are nearby clauses only, not proof of absence. Known limitation: the existing Contract v1 output becomes schema-valid only after human annotations are completed; the execution harness intentionally persists pre-review records rather than encoding pending judgments as invented `uncertain` labels. Security impact is limited to sending public policy excerpts/questions to OpenAI during a live run; the key is read from the environment and never persisted. No retrieval, reranking, embeddings, or existing contract/gold data changed.
* Exact next step: run only the frozen live calibration with `OPENAI_API_KEY='<set-in-shell>' PYTHONPATH=src python -m evaluation.oracle_generation_calibration --config configs/oracle_generation_calibration_v1.json --run-id <unique-live-run-id>`, then complete and adjudicate human review and verify deterministic Contract v1 aggregation before any full benchmark or Stage 2B generation run.

**Testing**

* ✅ `pytest -q` (62 passed)
* ✅ `python -m compileall -q src tests`
* ✅ `git diff --check`
* ✅ `PYTHONPATH=src python -m evaluation.oracle_generation_calibration --dry-run --run-id 20261005T000000Z_dry_run_v1` (10 questions validated; zero API calls)
* ⚠️ `if [ -n "${OPENAI_API_KEY:-}" ]; then echo OPENAI_API_KEY_PRESENT; else echo OPENAI_API_KEY_ABSENT; fi` (`OPENAI_API_KEY_ABSENT`; live calibration blocked by missing credential)
