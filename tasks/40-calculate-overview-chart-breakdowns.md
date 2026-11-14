## Title

Calculate chart trends and whole-window totals

## Specification

Follow the [seven Overview chart groupings](../specification/01-screens/030-content.md#3222-trends-and-charts) and the [statistics class design](../specification/02-architecture/02-design/020-backend-class-design.md#statistics-classes). This work is confined to analytics and has no code dependency on task 39 or the redesigned renderer.

## Work

- In [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py), keep the existing Project and Agent trend calculators. Use `UsageCalculator.groups()`, `_bucket()`, and `_measure()` for `AgentUsageByProjectOverTimeCalculator` and `ModelUsageOverTimeCalculator`, keyed by `(project_key, reporting_agent_name(row), bucket)` and `(None, model, bucket)` respectively. Use the existing reporting name precedence and recorded-clock bucket calculation.
- Reuse `ModelUsageCalculator` for whole-window model totals. Add whole-window project and agent calculators keyed only by `project_key` and `reporting_agent_name(row)` respectively. Leave the bucket empty for all three totals. Calculate totals directly from the filtered scope rows alongside the trends. Keep nullable counts, coverage rules, counter overlap exclusions, and bucket clipping. Reuse the existing `UsageMeasurement` representation, including the current model group key convention, and perform no additional source reads.
- Register **Agent by project over time**, **Model over time**, **By project**, and **By agent** in `StatsCalculation` so a single `calculate()` call returns them for **Full selected period** and **Since [marker]**. The existing **Model** entry supplies the **By model** chart. Leave the existing registry entries in place while the Usage view control still calls them. Task 41 retires the unused whole-window **Agent by project** breakdown with its caller.
- Keep filters, scope boundaries, ingestion, schema, and the existing scope summary unchanged. Leave display and CSV changes to task 41.

## Acceptance Criteria

- In each reporting window the seven chart groupings use the same eligible rows. Verify with multiple projects, agents, and models across several buckets, including one reporting agent appearing under two projects and two executions sharing one reporting name.
- Hourly, daily, weekly, and monthly selections change trend buckets. Per-model, per-project, and per-agent totals stay identical across bucket sizes for the same filtered window and keep unknown totals distinct from zero.
- A marker inside a bucket changes the eligible usage for trends and totals under **Since [marker]**. Existing selectors still work after this task and the scope summary and coverage behavior remain intact.
