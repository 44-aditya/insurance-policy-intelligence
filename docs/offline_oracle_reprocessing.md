# Offline oracle calibration reprocessing

After installing the project (`python -m pip install -e '.[test]'`), run:

```bash
reprocess-oracle-calibration \
  artifacts/generation/oracle_calibration/20261010_oracle_gpt54_calibration_v5 \
  --output-dir artifacts/generation/oracle_calibration/20261010_oracle_gpt54_calibration_v5_reprocessed
```

Alternatively use `python -m evaluation.reprocess_oracle_calibration` with the
same arguments. The destination must be new and separate from the source;
existing directories, source ancestors, and source descendants are rejected.
The command only reads local files. It does not instantiate an OpenAI client,
download anything, or execute a live calibration.

The source needs `run_manifest.json`, `generation_records.json`, and serialized
Responses API objects at `raw_responses/<question_id>.json`. The CLI extracts
completed message `output_text` content and passes it to the current
`parse_structured_output()` with the **saved record's** context IDs. Ordered
`cN`, `fcN`, and `claim_N` aliases become canonical `CN`; duplicate, misordered,
or ambiguous IDs and invalid citations still fail. Refusals and incomplete
responses are failures. Missing or corrupt raw files produce per-record failures
without preventing other records from being processed.

The derived directory contains:

- `run_manifest.json`: source run ID/path, a verbatim source manifest object,
  structural reprocessing counts, and zero new API calls and estimated API cost.
- `generation_records.json`: revalidated answers and canonical claims, original
  model/prompt/schema/evaluator versions, prompts, evidence, rubric and usage;
  per-record `reprocessing` metadata includes the raw path and SHA-256, original
  failure/status/usage, raw response usage, claim-ID mapping, and outcome.
  Remaining failures appear in `failure` with stage `offline_reprocessing`.
- `human_review.md`: regenerated worksheet with canonical claims and blank
  semantic labels. Prior human review is not carried forward as a new judgment.

Original accounting is never recomputed or overwritten. In the live harness,
parsing failures can leave a record's token/cost fields at zero even after a paid
call. `reprocessing.raw_response_usage` exposes the provider's saved usage
separately; it does not change the source estimate or imply those calls were
free. Record latency remains the original measured latency. Offline processing
adds zero inference cost. No correctness or faithfulness scores are assigned.

Exit status is 0 when every record revalidates, 1 when the derived run contains
record failures, and 2 for run-level input or destination errors. Source files
and raw responses are never written; raw symlinks escaping the source run are
rejected. Treat the derived directory as a new review artifact, not a replacement
for the original experiment.

Validation: the full suite passed **100 tests**. Offline fixtures cover all three
alias families, complete source byte immutability, provenance/accounting,
missing/corrupt raw files, invalid citations, duplicate/misordered IDs, refusal
and incomplete responses, continued processing after failures, destination
guards, and CLI exit statuses. Network connections and OpenAI client creation
are forbidden in these tests. The v5 live run is absent from the cloud checkout;
its three reported failures have not been reprocessed here. No new live run was
executed.
