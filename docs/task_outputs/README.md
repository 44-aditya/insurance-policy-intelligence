# Codex task outputs

This directory preserves the complete final response/output of every material
Codex task, essentially verbatim. It lets the project owner, ChatGPT, and future
agents inspect previous work without manually transferring responses. It is an
agent work log, not recruiter-facing documentation.

## Recording a task

1. Save the complete final response after material implementation, investigation,
   experiment, evaluation, or decision work. Routine acknowledgments and trivial
   status checks do not require a record.
2. Use `YYYY-MM-DD_NNN_short-task-description.md`, using the project owner's local
   date and the next available three-digit sequence for that date. Never overwrite
   an earlier task record. Record the date of the response, which may differ from
   the experiment's timestamp.
3. Begin with only the metadata needed for provenance:

   ```markdown
   - Date: YYYY-MM-DD
   - Task / purpose: Brief task description
   - Git branch: branch-name
   - Related PR: #N, or unknown / none
   - Commit SHA: applicable source revision, or not applicable
   - Output status: Raw/verbatim (list any portability changes or redactions)

   ---

   Complete final task response follows here.
   ```

4. Preserve technical details, tables, measurements, caveats, diagnostics, failure
   classifications, and recommendations. Do not replace them with a summary.
   Replace machine-specific links with repository-relative links where necessary;
   explicitly record any other necessary redactions or departures from verbatim.
5. Never store credentials, secrets, API keys, environment-variable values, or
   other sensitive information. Redact sensitive content before saving and mark
   the redaction without retaining the sensitive value.
6. Save the task record before delivering the final response. Keep its response
   body aligned with the actual final response, including validation outcomes.
   Metadata describes the inspected revision, not an uncreated future commit.

Unavailable historical responses must not be fabricated or reconstructed and
labelled raw. Add a historical response only when its original output is available;
identify its original date and the later capture date when applicable.

## Relationship to other records

- [Timelapse](../timelapse.md) curates the engineering, product, learning, and
  decision narrative. Material milestones also belong there.
- Formal experiment artifacts and reports remain authoritative for reproducible
  metrics. A task response records what the agent said, including its limitations;
  it does not silently supersede measured results.
- Preserve later corrections as explicitly identified follow-up records rather
  than rewriting an earlier response to make history appear more successful.

The first record captures the available 2026-10-04 unmatched-evidence analysis.
No unavailable earlier Codex responses have been reconstructed.
