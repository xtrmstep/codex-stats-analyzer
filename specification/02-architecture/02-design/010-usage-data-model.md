# Usage data model

The local SQLite model holds collected source records, derived usage, and user-authored time markers. Reporting requests and measurements live in memory. See the [system overview](./000-system-overview.md) for collection and rebuild behavior and the [backend class design](./020-backend-class-design.md) for the components that operate on these records.

## CollectedCodexRecord

One record holds one original JSONL line. It stores a stable record ID, source log identity, source path at collection, line number, exact original line bytes including its terminator when present, and collection timestamp. The source log identity survives a verified append or archive move under the [raw collection rules](./000-system-overview.md#raw-collection).

## CodexAgentThread

One record represents one resolved agent execution. It stores the execution identity, native thread ID, session ID, parent thread identity when verified, and observed agent name, role, or nickname when available.

Preserve `session_id` and `thread_id` separately. A verified parent link is optional, including when the parent was omitted from the import. Session ID supports conversation grouping where the source establishes it. Use the configured agent name or role to group executions across chats. A nickname can identify an individual execution in the UI.

## CodexUsage

One record represents a reported response or one legacy counter delta. It stores a stable usage identity, owning thread when verified, observed timestamp, project key and display label when known, model when supported by the matched context, coverage, and a reference to the collected record. Keep enough counter provenance to distinguish independently attributable usage from counters whose scopes may overlap. The nullable counts are input, output, cached input, cache-write input, reasoning output, and total tokens. Legacy deltas also retain the prior observation time when known.

Match turn context by thread and turn ID where available. Derive project attribution from that turn's working directory, with the owning thread's working directory as a fallback. Use a normalized repository identity where metadata supports it so worktrees of the same repository group together. Use the normalized working directory when a repository identity is unavailable. Retain the source working directory for inspection. Missing project, model, or agent attribution remains visible as unknown.

## TimeMarker

One record stores a stable identifier, user-entered name, and timestamp. Saved markers survive usage rebuilds and schema upgrades. See [saved time markers](../../codex-usage-analyzer.md#54-saved-time-markers) for product behavior.

## StatsRequest

One request carries the selected filters, reporting bounds and time zone, optional saved `TimeMarker`, time bucket size for time-series views, and whether to group agents by execution or name or role. The calculation manager resolves the [reporting windows](../../codex-usage-analyzer.md#63-visualizations) once and supplies the same filters and windows to each calculator.

## UsageMeasurement

One measurement represents a summary or a single group in one reporting window. It carries the scope (full selected period or since marker), effective bounds, project or agent grouping keys where applicable, and an optional time bucket. It returns token totals, cache percentage, and average tokens per day with complete, partial, or unknown coverage for the applicable values. A result identifies an empty reporting window explicitly. Unknown amounts remain distinct from zero.

Calculators return measurements to the caller. Measurements are calculated on demand from the committed inputs and kept in memory for the current report.

## Storage conventions

Store timestamps in UTC and apply the dashboard time zone for date selection and display. Store observations at their original granularity so any saved timestamp can serve as a cutoff. Compute report totals and averages from usage rows when queried. The initial schema needs no project, model, conversation, or precomputed summary tables.
