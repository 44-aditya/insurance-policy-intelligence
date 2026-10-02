# Stage 1 source corpus

## Scope

Stage 1 is intentionally limited to official **Policy Wording** documents published by Tata AIG General Insurance Company Limited for these products:

- Tata AIG MediCare Premier
- Tata AIG MediCare Select
- Tata AIG MediCare Reserve
- Tata AIG MediCare Plus

Policy Wordings are the authoritative contractual source for the first retrieval experiment. Keeping the source class narrow makes retrieval and answer-grounding results easier to interpret: a failure can be investigated against one defined document type rather than against overlapping documents with different purposes or levels of detail.

Customer Information Sheets (CIS), prospectuses, brochures, and FAQs are excluded from this initial corpus. Those documents may simplify, select, or present information differently from the Policy Wording and could introduce duplicate or conflicting passages into the first experiment. This is an **experimental design choice**, not a permanent product decision or a claim that those materials lack value. Later experiments may add one source class at a time and measure its effect on recall, ranking, answer correctness, faithfulness, citation accuracy, latency, token use, and cost.

No document in this directory may be treated as policy advice. The corpus exists for controlled technical evaluation.

## Layout

```text
corpus/
├── README.md
├── metadata.json
└── policy_wordings/
```

`policy_wordings/` is reserved for byte-for-byte copies of PDFs downloaded from the official Tata AIG Downloads page. PDFs must not be optimized, rewritten, OCR-replaced, annotated, or otherwise modified. No chunked text, embeddings, vector database files, generated questions, or document summaries belong in this corpus.

## Provenance and versioning

A document is eligible only when both the Tata AIG Downloads page and the PDF itself support that it is the Policy Wording for the intended product. A product-page link, search result, filename, or document title alone is not sufficient when the identity is ambiguous.

For every admitted PDF, `metadata.json` must record:

- insurer;
- product name;
- document type;
- UIN, version, and effective/version date only when explicitly stated by the official source or document;
- the direct official source URL;
- the UTC download date;
- the repository filename; and
- the SHA-256 digest of the preserved bytes.

Unknown fields must be `null`; values must never be inferred from naming patterns or from another edition. A replacement edition is added as a new, separately checksummed artifact rather than silently overwriting the existing file. Metadata changes and PDF changes are committed together so Git history preserves the acquisition record.

Verification should include PDF-format identification, extraction or visual inspection of the title/UIN pages, comparison with the label on the official Downloads page, and recomputation of every SHA-256 digest. Redirect destinations should be retained as provenance if they differ from the published link.

## Acquisition status and ambiguity

No PDF has been admitted in this revision. On 2026-10-02, the execution environment could not access the official Tata AIG Downloads page: direct HTTPS access was rejected by the environment's network proxy, and the provided web-access service returned an authorization error. Consequently, the current official links, editions, document contents, and metadata could not be verified without relying on an unapproved third-party source or guessing.

`metadata.json` therefore contains an empty `documents` array rather than unsupported records. The four expected products are recorded separately as pending acquisition targets. This repository must not represent the corpus as complete until all four official PDFs have been downloaded and verified.
