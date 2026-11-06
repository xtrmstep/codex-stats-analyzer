# 13 — Consistent refresh and CSV export

Status: Not started | Phase: 3 | Dependencies: 06, 10, 12

Specification: §§3.1, 6.3, 7.4; MVP 10, 11.

## Scope

- Add explicit refresh for new, appended, archived, changed and unavailable source files without a background service.
- Invalidate derived caches consistently and preserve labels, run references and saved comparison definitions.
- Surface truncated trailing lines, changed sources and missing references without duplicating events or corrupting prior annotations.
- Export filtered session/run tables and comparison results to CSV with stable column names, units, unknown values, and relevant provenance/estimate indicators.
- Ensure CSV respects the selected filters/grouping and uses documented Windows-friendly Unicode encoding and timestamp formatting.

## Acceptance and validation

- Refresh after appending events and archiving a source: counts, references, runs and experiments remain consistent.
- Repeated refreshes are idempotent; source contents and modification times remain unchanged.
- Compare exported values with on-screen results under combined filters; check Unicode, commas, quotes, newlines and unknown values.
