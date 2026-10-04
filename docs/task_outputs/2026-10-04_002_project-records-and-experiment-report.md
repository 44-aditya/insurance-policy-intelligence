- Date: 2026-10-04
- Task / purpose: Establish raw task-output and curated timelapse conventions; document completed Experiment 1 and prepare an unstaged review diff
- Git branch: codex/implement-stage-1-semantic-vector-retrieval
- Related PR: #10 — https://github.com/44-aditya/insurance-policy-intelligence/pull/10
- Commit SHA: a08481a3a0f21c3bb219ffe169acd3ca047098a8 (source revision; proposed changes are uncommitted)
- Output status: Raw/verbatim; the machine-specific temporary diff link was replaced with its filename for repository portability during final review.

---

Implemented the permanent logging convention and updated Experiment 1’s report. The previous root-cause response is preserved in full, with portable links; this task’s final response is also saved.

**Complete diff for review: `stage1-project-records-review.diff` (temporary review artifact)** includes every proposed file, including new files and the pre-existing measured results/chunks. Nothing is staged, committed, or pushed.

Proposed commit: **`Preserve agent outputs and project learning; document Stage 1 results`**

Proposed contents:

- `.gitignore` — exclude `vectors.json`; retain the local cache.
- `AGENTS.md` — permanent raw-output, timelapse, metric-authority, and security rules.
- `docs/task_outputs/README.md` — filename, metadata, preservation, and redaction conventions.
- `docs/task_outputs/2026-10-04_001_unmatched-evidence-root-cause-analysis.md` — complete prior analysis.
- `docs/task_outputs/2026-10-04_002_project-records-and-experiment-report.md` — this response.
- `docs/timelapse.md` — evidence-supported historical entries labelled reconstructed, plus contemporaneous findings and decisions.
- `docs/stage1_semantic_retrieval_report.md` — original measured metrics, operational measurements, mapping limitations, and next steps.
- `artifacts/retrieval/stage1_voyage4/retrieval_results.json` — original completed result, unchanged by this task.
- `artifacts/retrieval/stage1_voyage4/chunks.jsonl` — existing 360-chunk snapshot for inspecting the recorded run.

Validation: **25 tests passed** with five dependency deprecation warnings. Diff whitespace checks and local documentation links passed; recorded input fingerprints match. No packages were installed or paid API calls made. Gold, extraction, chunking, evaluator, and retrieval implementation were untouched.

The report retains the original K=10 Recall **0.5925925925925926** and Sufficient Evidence **0.46153846153846156**, while explaining why architectural conclusions remain provisional. Estimated original run cost remains **$0.00906792**; this task added no API cost. No credentials or sensitive values were added.

Historical narrative is reconstructed from repository evidence, not fabricated raw responses. The next step remains human PDF review and an explicit evaluation-contract decision before rescoring or changing architecture.
