# Backend class design

## Import classes

| Class | Responsibility |
| --- | --- |
| `CodexLogImporter` | Collects and stores original records on refresh, runs registered transformations on a committed snapshot, reports diagnostics, and controls atomic publication. |
| `CodexLogReader` | Discovers configured files and yields original lines with source positions, or reads an ordered SQLite snapshot through the same interface. |
| `CodexRecordTransformation` | Defines an output type, destination mapping, and parser that turns an ordered snapshot into rows and diagnostics. |
| `DatabaseWriter` | Uses Python's `sqlite3` to write collected records, transformed rows, and markers through destination mappings. |

```mermaid
classDiagram
    CodexLogImporter *-- CodexLogReader : one reader
    CodexLogImporter *-- CodexRecordTransformation : registered transformations
    CodexLogImporter *-- DatabaseWriter : one writer
```

Register [`CodexAgentThread`](./010-usage-data-model.md#codexagentthread) and [`CodexUsage`](./010-usage-data-model.md#codexusage) through the same transformation interface and share identity rules and parsing helpers. Parsers may consult multiple records for identity, turn context, or legacy deltas. The writer provides transaction operations, and the importer sets publication boundaries. Keep schema definitions and versioned upgrades with the model's SQLite setup. See [collection and rebuild](./000-system-overview.md).

## Statistics classes

| Class | Responsibility |
| --- | --- |
| <a name="statscalculation"></a>`StatsCalculation` | Resolves windows once per [request](./010-usage-data-model.md#statsrequest), shares filters and one committed read snapshot, and assembles results. |
| <a name="usagecalculator"></a>`UsageCalculator` | Reads committed rows through the report connection and returns [measurements](./010-usage-data-model.md#usagemeasurement) using shared aggregation. |
| `ProjectUsageOverTimeCalculator` | Reads `CodexUsage` and groups by project and time bucket. |
| `AgentUsageOverTimeCalculator` | Reads `CodexUsage` and `CodexAgentThread` and groups by agent and time bucket. |
| `AgentUsageByProjectCalculator` | Reads `CodexUsage` and `CodexAgentThread` and groups by agent and project. |

```mermaid
classDiagram
    StatsCalculation *-- UsageCalculator : registered calculators
    UsageCalculator <|.. ProjectUsageOverTimeCalculator
    UsageCalculator <|.. AgentUsageOverTimeCalculator
    UsageCalculator <|.. AgentUsageByProjectCalculator
```

Use shared rules for token totals, overlap, coverage, weighted cache percentage, and daily averages. Calculate window summaries directly from eligible rows. Clip time buckets to the reporting window. Mark empty windows explicitly and keep unknown amounts distinct from zero. Coverage can be complete, partial, or unknown. See [reporting windows](../../codex-usage-analyzer.md#63-visualizations).

## Existing code

| Component | Responsibility |
| --- | --- |
| `parser.py` and `Event` | Parse and normalize timestamps, IDs, counters, context, and relationships independently of SQLite and the dashboard. |
| `analytics.py` and `agents.py` | Normalize usage, calculate deltas, and resolve threads in functions. Extend `Increment` with response counts, legacy deltas, and provenance. Use the resolved `Agent` identity for accounting and hierarchy. |
| `metrics.py`, `Filters`, and `Metrics` | Reuse filtering and coverage-aware aggregation. Dashboard and export use the same measurements. |
| `app.py` and `dashboard.py` | Compose the importer and calculators, run collection and rebuild on refresh, show committed results and diagnostics, and manage saved markers. |
| Annotation storage | Retains session labels and other user metadata. |
