- Date: 2026-10-04
- Task / purpose: Prepare the Evaluation Contract v2 authoritative-evidence human-review package
- Git branch: docs/evaluation-contract-v2-human-review
- Related PR: unknown / pending creation
- Commit SHA: 176dee03470d806ef22bd2c7a1fe8c455d14ee82 (source revision)
- Output status: Raw/verbatim; PR metadata was not yet available when this in-commit record was created

---

### Summary

* Prepared the owner-review package for all 18 unmatched spans, with verbatim current gold, visually adjudicated PDF evidence, layer-specific failure explanations, atomic units/fragments, sufficiency rationales, stored retrieval observations, and `PENDING` decisions. The package explicitly preserves the chain from source truth through evaluator and does not calculate corrected Recall@K. 【F:docs/evaluation_contract_v2_review.md†L3-L30】
* Classified the proposals as 2 annotation corrections, 9 decompositions, 5 evaluator-only changes, and 2 negative-space cases; identified Q002 and Q034 as the remaining genuine Top-10 retrieval misses after the proposed corrections. 【F:docs/evaluation_contract_v2_review.md†L335-L382】
* Recorded the new visual-PDF findings in the timelapse: Q002 requires a transcription correction, Q034 requires a page-14/page-15 locator correction, and Q038’s `maximum` wording is already source-correct despite fragmented extraction. No gold, schema, evaluator, extraction, chunk, embedding, retrieval implementation, or stored result was modified. 【F:docs/timelapse.md†L204-L235】
* Preserved the full task response in this task-output record and documented the zero-paid-API constraint, limitations, security/cost implications, and recommended post-approval calibration experiment. 【F:docs/evaluation_contract_v2_review.md†L398-L414】

**Testing**

* ✅ `python -c 'from pathlib import Path; p=Path("docs/evaluation_contract_v2_review.md").read_text(); fields=("Question ID","Question","Current gold","Authoritative PDF evidence","Problem","Proposed atomic unit(s)","Proposed source fragment(s)","Required for sufficiency?","Retrieval observation","Reviewer decision"); assert all(p.count(f"| {x} |") == 18 for x in fields); assert p.count("| Reviewer decision | `PENDING` |") == 18; assert "**Total** | **18**" in p'`
* ✅ `git diff --check`
* ✅ `pytest -q` (25 passed)
* ⚠️ `command -v markdownlint` (not installed; the repository provides no documentation/link checker, and the new review document contains no Markdown links)
