## Title

Calculate and display independent token usage per agent

## Goal

Provide accurate token usage metrics for each Codex agent and subagent independently, without combining counters across agents.

Clearly explain that combined totals and subagent share cannot be calculated reliably because parent counters may already include child-agent usage.

## Work

Review and adjust token accounting and dashboard presentation in the [codex-stats-analyzer](https://github.com/xtrmstep/codex-stats-analyzer?utm_source=chatgpt.com) repository.

### 1. Independent agent accounting

Each detected agent, including the parent (orchestrator) and nested subagents, should have its own reported token metrics:

- Total, input, output, and cached tokens.
- Cache percentage.
- Existing completeness and partial-coverage indicators.
- Agent role, model, and identifier.

Accumulate token increments only within the same agent's counter stream. Never sum token counters belonging to different agents, even when they are siblings rather than parent and child.

Reported parent usage must not be described as exclusive parent consumption.

Technical references:

- `analytics.py` — `calculate_increments()`, `aggregate()`
- `agents.py` — `analyze_agents()`
- `metrics.py` — `summarize()`, `build_dataset()`

In `analytics.py`, the current aggregation guard is:

```
if len(agents) > 1 and any(    i.parent_agent_id in agents for i in increments):    return {        key: Total(None, False)        for key in (*fields, "cache_percentage")    }
```

This prevents some parent-child aggregation but does not prohibit combining unrelated or sibling agent streams.

Review this behavior together with `_overlapping_streams()` in `metrics.py` to ensure that no cross-agent total is presented as reliable.

Preserve the existing cumulative-counter handling, reset detection, missing-value handling, and coverage rules.

### 2. Agent hierarchy metrics

In `agents.py`, individual metrics are already assigned:

```
totals = aggregate([    i for i in increments    if i.session_id == agent_id])agent.tokens = totals["total_tokens"]agent.cache_percentage = totals["cache_percentage"]
```

Verify that these counters are attributed to the correct agent/thread and that multiple counter families are not combined.

The existing `AgentAnalysis` also exposes:

```
main_tokens: Totalsubagent_tokens: Totalsubagent_share: Total
```

Review these fields and any consumers to remove unsupported combined-agent accounting.

### 3. Dashboard presentation

Relevant code: `dashboard.py`, especially `details()` and the main KPI section.

Display separate metrics for each agent in the hierarchy.

Example presentation:

| Agent        | Model | Total tokens | Input  | Output | Coverage |
| ------------ | ----- | ------------ | ------ | ------ | -------- |
| Orchestrator | Sol   | 100,000      | 85,000 | 15,000 | Complete |
| Developer    | Terra | 40,000       | 32,000 | 8,000  | Complete |
| Reviewer     | Astra | 20,000       | 16,000 | 4,000  | Partial  |

Illustrative values.

Remove the `Subagent share: Unknown` KPI and avoid combined parent/subagent totals or charts.

When multiple agents are selected, individual metrics must remain accessible, but no combined token total should be displayed.

Review other affected views, including overview KPIs, project/model/session breakdowns, time charts, and CSV exports, so they do not expose misleading cross-agent totals.

Add a concise explanation near agent metrics:

> Agent token usage is reported independently. Combined totals and subagent share are unavailable because parent counters may already include child-agent usage. Individual values may overlap and must not be added together.

### 4. Maintain existing filtering and coverage

Agent metrics should respect the existing project, model, session, agent, and time filters.

Preserve the distinction between:

- Complete — all required counter data is reliably available within the selected scope.
- Partial — some reported usage is available, but coverage is incomplete.
- Unknown — no reliable value can be calculated.

Missing token counters must not become zero.

Review `metrics.py` and `dashboard.py` to ensure consistency between hierarchy metrics, filters, and displayed results.

Update the relevant specification to reflect independent agent accounting.

## Acceptance Criteria

- Each observed agent has independently calculated token metrics based only on its own attributed counter stream.
- Parent, child, nested subagent, and sibling counters are never summed into a combined total.
- Selecting a single agent shows its available token metrics and correct coverage indicators.
- Selecting multiple agents does not produce a misleading combined token total.
- The agent hierarchy displays individual total, input, output, and cache metrics, with coverage information.
- The `Subagent share` KPI and unsupported combined-agent charts are removed.
- The explanation of possible counter overlap is visible in the dashboard.
- Project, model, session, time-based, and export views follow the same accounting rules.
- Existing handling of cumulative counters, resets, invalid counters, and missing data is preserved.
- Missing or incomplete agent data is clearly identified rather than represented as zero or complete.
- Existing tests, if available, continue to pass; static review confirms that no cross-agent aggregation paths remain.
- Relevant specifications reflect the updated accounting behavior.

## Follow-up

This task applies conservative accounting to the existing counter streams. [Task 19](./19-sessions-analytics-improvement.md) adds combined totals only for usage whose counter scopes are verified to be independent.
