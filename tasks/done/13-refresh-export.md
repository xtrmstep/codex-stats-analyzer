# 13 — Consistent refresh and CSV export

Status: Complete; independent review passed | Phase: 3 | Dependencies: 06, 10, 12

Specification: §§3.1, 6.3, 7.4; MVP 10, 11.

## Scope

Review: independent Astra re-review passed at `180c33d`, including committed run attribution in display and CSV. Browser downloads remain for task 14.

- Add explicit refresh for new, appended, archived, changed and unavailable source files without a background service.
- Invalidate derived caches consistently and preserve labels, run references and saved comparison definitions.
- Surface truncated trailing lines, changed sources and missing references without duplicating events or corrupting prior annotations.
- Export filtered session/run tables and comparison results to CSV with stable column names, units, unknown values, and relevant provenance/estimate indicators.
- Ensure CSV respects the selected filters/grouping and uses documented Windows-friendly Unicode encoding and timestamp formatting.

## Acceptance and validation

- Refresh after appending events and archiving a source: counts, references, runs and experiments remain consistent.
- Repeated refreshes are idempotent; source contents and modification times remain unchanged.
- Compare exported values with on-screen results under combined filters; check Unicode, commas, quotes, newlines and unknown values.

## Decisions and validation evidence

- Explicit refresh rereads local sources; no derived analytics are cached between Streamlit reruns. SHA-256 path fingerprints report newly discovered, changed and missing/moved sources relative to the previous refresh. The parser reports malformed or truncated lines; unavailable annotation sessions and run boundary references are surfaced separately. Metadata and comparisons are not rewritten by refresh.
- Session, run and current comparison downloads use the same filtered rows as their displayed tables. CSV has stable snake_case headers, UTF-8 BOM and CRLF for Windows, standard CSV quoting, blank unknown values, UTC ISO 8601 timestamps where applicable, units and provenance/coverage columns. Comparison export follows selected groups and metrics; run and label groups can overlap and are not additive.
- Inline synthetic checks passed unchanged/idempotent refresh, appended counter, archive relocation with stable event references, unchanged source hashes/mtimes during reads, metadata preservation, and CSV roundtrip for Unicode, commas, quotes, newlines, unknowns and displayed token values. Python modules compiled. Actual browser download and offline interaction remain unverified; independent review pending.

