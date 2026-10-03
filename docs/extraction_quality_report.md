# Baseline PDF extraction quality report

## Experiment and decision

This experiment asks whether PyMuPDF's default page-level plain-text extraction
is sufficiently faithful to serve as the first Stage 1 retrieval baseline. It
does not test retrieval. PyMuPDF was selected because it reads PDFs locally,
exposes page boundaries directly, and requires neither OCR nor a
document-processing framework.

**Result:** the evidence supports PyMuPDF as an adequate *experimental Stage 1
baseline*, but not as a uniformly faithful or production-ready representation.
The three newer single-column policy wordings preserve prose, headings, clauses,
bullets, and simple tables well enough to begin measured retrieval experiments.
MediCare Plus has substantially poorer source encoding/layout: its two-column
text is generally ordered correctly, but words are sometimes split internally,
table cells are flattened, and pages 8 and 21 contain large runs of spurious
characters after otherwise useful text. Those defects must remain visible in
downstream evaluation and may justify a separately measured parser/layout
experiment if they cause retrieval failures. The human architect retains the
final decision.

## Run configuration and measured results

The committed artifacts were generated on 2026-10-03 with Python 3.14.4 and
PyMuPDF 1.28.2 by running `extract-policy-pages` from the repository root. No
fallback parser was used.

| Policy | PDF pages | Blank extracted pages | Extracted characters |
| --- | ---: | ---: | ---: |
| TATA AIG MediCare Select | 44 | 0 | 126,622 |
| TATA AIG MediCare Plus | 26 | 0 | 87,942 |
| TATA AIG MediCare Premier | 60 | 0 | 154,923 |
| TATA AIG MediCare Reserve | 40 | 0 | 130,701 |
| **Total** | **170** | **0** | **500,188** |

- PDFs discovered: **4**
- PDFs processed: **4**
- Page records written: **170**
- Extraction errors: **none reported by PyMuPDF**
- Paid API usage: **none; zero external API cost**

These counts establish coverage, not accuracy. The visual checks below compare
rendered source pages with their corresponding JSONL `text` values.

## Representative visual inspection

### TATA AIG MediCare Select

Reviewed PDF pages **2, 12, 18, and 33**.

- Page 2 (definitions) preserves the `Section 1 – Definitions` heading,
  introductory prose, numbered definitions 1–4, and nested roman/alphabetic
  lists in the correct sequence. Bold styling is lost, as expected.
- Page 12 (normal benefit prose) preserves B1–B4 headings, numbered expense
  items, nested item `ii.a`, and two bullet points in readable order.
- Page 18 (structured Early Access benefit) preserves prose and all table cell
  values. The grid and merged cells are lost: the two `60 Lakhs` cells appear in
  the text stream after `Year 1` and `Year 4`, so the visual grouping across
  three-year blocks must be inferred rather than represented explicitly.
- Page 33 (claims tables) emits headers followed by cells in row order, but
  wrapped cell text becomes many short lines. The table remains interpretable
  to a person, although column relationships are implicit and therefore more
  fragile for retrieval.
- The complete company/contact/UIN/page footer is extracted before body content
  on every one of the 44 pages. This is substantial repeated-header/footer
  pollution, intentionally retained for this baseline.

### TATA AIG MediCare Plus

Reviewed PDF pages **2, 8, 20, 21, and 26**.

- Page 2 contains preamble prose in the left column followed by definitions,
  then continues at the top of the right column. PyMuPDF follows that intended
  column order and keeps clause numbering, but the source itself uses tight
  typography and the extraction includes malformed spacing such as
  `ins ur a nee co mpa ny's`, `Governmenu`, and concatenated words.
- Page 8 preserves B7–B12 in left-column-then-right-column order, including the
  numbered illness list. It also splits many words internally (`sha ll`,
  `hosp ital`, `l i m it`) and appends 2,021 characters after the footer of
  meaningless isolated punctuation/letters not visible as policy text. This is
  an obvious extraction failure, despite the valid policy text preceding it.
- Page 20 combines a four-column cashless-service table with two-column prose.
  Text from the table is interleaved with the procedure below it: table payment
  and notice cells appear partway through clause `3.ii.e`. The text is present,
  but its semantic reading order is wrong. Widely spaced words such as
  `t r e a t m e n t` further reduce fidelity.
- Page 21 keeps the visible two-column supporting-documentation clauses in
  column order, but, like page 8, appends a large block of spurious isolated
  characters (1,679 characters after the footer). Pages 8 and 21 are the two
  clearest malformed-character failures in the corpus.
- Page 26 extracts the Ombudsman table row-by-row with all visible office values.
  The two-column statutory prose below the table follows left column then right
  column correctly, but table structure and column labels are flattened.
- Company/contact/UIN/page furniture occurs on all 26 pages and is retained.
  Page 1 also contains a form-feed control character. No replacement-character
  glyphs (`U+FFFD`) were observed; the more important defect is spurious valid
  punctuation/letters and intra-word spacing.

### TATA AIG MediCare Premier

Reviewed PDF pages **2, 12, 14, and 20**.

- Page 2 preserves preamble prose, the general-definitions heading, numbered
  definitions, and the beginning of definition 3 in the same order as the PDF.
- Page 12 preserves normal prose, six bullet items, B4/B5 headings, and nested
  roman conditions. Paragraph and bullet boundaries remain distinguishable.
- Page 14 preserves both two-column-value tables in row order (AYUSH
  post-hospitalization days and ambulance limits). Borders and cell geometry are
  lost, but each key is followed by its corresponding value; excess whitespace
  appears around the centered AYUSH line.
- Page 20 similarly preserves maternity and delivery-complication table rows,
  followed by the correct exclusions and bullet list. Relationships are readable
  for these simple two-column tables, though not structurally encoded.
- Company/contact/UIN/page furniture precedes the body on all 60 pages. No
  obvious missing text, malformed glyphs, or body reading-order reversal was
  observed in the sampled pages.

### TATA AIG MediCare Reserve

Reviewed PDF pages **2, 12, 32, and 33**.

- Page 2 preserves the definitions heading, definitions 1–4, and nested lists in
  the source order.
- Page 12 preserves normal benefit prose, roman and alphabetic lists, bullets,
  and B2–B5 headings. It starts mid-B1 because the source page itself continues
  from the prior page; no additional discontinuity was introduced.
- Page 32 preserves the three-column zone/co-payment table in row order and then
  resumes clauses 23–24 correctly. Grid geometry is lost, but the compact rows
  remain unambiguous.
- Page 33 preserves the claims heading and prose. Its first table remains
  understandable in row order; the second wider table is flattened into headers
  and wrapped cell fragments, so column association is only implicit.
- Company/contact/UIN/page furniture precedes body content on all 40 pages. No
  obvious malformed glyphs or prose-order errors were observed in the sample.

## Cross-corpus findings and limitations

1. **Headings and clauses:** headings, clause identifiers, numbered definitions,
   roman lists, alphabetic lists, and bullet markers are generally retained.
   Typography (bold, font size, shading) is not retained.
2. **Tables:** no table schema, borders, merged-cell spans, or coordinates are
   represented in JSONL. Simple tables usually flatten into usable row order;
   merged and wide tables lose explicit relationships. MediCare Plus page 20 has
   a concrete interleaving/reading-order failure.
3. **Headers and footers:** publisher/contact/UIN/page furniture is present on
   every page in every document (170/170). In Select, Premier, and Reserve it is
   emitted before body text even though it is visually at the bottom. It will
   create repetitive retrieval terms until a later, separately evaluated cleanup
   experiment is approved.
4. **Malformed content:** no pages are blank and no parser exceptions occurred,
   but that does not imply fidelity. MediCare Plus pages 8 and 21 contain large
   spurious character blocks; other Plus pages show intra-word spacing and
   occasional malformed words. No `U+FFFD` replacement glyphs were found.
5. **Reading order:** sampled single-column prose is ordered correctly. The Plus
   two-column pages normally read left column then right column, while its page
   20 table/prose combination interleaves unrelated regions. Tables elsewhere
   are plain sequences rather than structured rows and columns.
6. **OCR:** none was used. All 170 pages returned text, so there is no evidence
   that an OCR experiment is required for this corpus.

## Cost, security, and recommended next experiment

This experiment used only local, repository-controlled public policy documents.
It made no API or LLM calls, introduced no credentials, and incurred no paid API
cost. Generated text is stored under `artifacts/extraction/`, outside the
authoritative raw PDF directory.

The next experiment should use this unchanged output in the planned Stage 1
retrieval evaluation and stratify failures by document/page, especially
MediCare Plus pages 8, 20, and 21 and table-dependent questions. Measure
Recall@K, ranking quality, answer correctness, faithfulness, citation accuracy,
latency, tokens, and cost before proposing cleanup or a layout-aware parser. If
these known defects measurably cause retrieval failures, compare one narrowly
defined alternative against this committed baseline rather than silently
changing extraction behavior.
