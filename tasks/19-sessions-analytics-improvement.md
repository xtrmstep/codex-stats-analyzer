## Title

Support conversation-level token accounting and agent aggregation by name and model

## Goal

Provide accurate Codex token analytics at two levels: complete conversations, including their subagents, and individual agents across conversations.

Allow users to aggregate agent consumption by agent name or by agent name and model, including cases where the same agent uses different models over time.

## Work

### 1. Separate conversation and agent identities

Review how Codex JSONL files identify conversations, threads, and parent-child relationships.

- Treat a conversation as the logical chat containing the main agent and its related subagents.
- Identify each agent execution independently, even when multiple threads belong to one conversation.
- Preserve agent name, role, parent, model, and project metadata.
- Support nested subagents and existing session formats.
- Do not merge unrelated threads when relationships cannot be established.

Technical hints:

- `parser.py`: `Event`, `_normalize()`, `ingest()`.
- `session_meta` currently uses `payload.session_id` or `payload.id` as one identifier.
- `token_usage_record` may contain explicit `thread_id` and `session_id` fields that are not currently preserved separately.
- `agents.py`: `analyze_agents()` currently uses `event.session_id` as the agent identity.
- Existing event references and saved annotations must remain valid where possible.

### 2. Correct token accounting

Calculate usage independently for each agent thread and support conversation-level totals across related threads.

- Distinguish per-response usage from cumulative thread counters.
- Avoid double-counting repeated cumulative observations.
- Include main-agent and subagent consumption in conversation totals only when counter scopes are known to be independent.
- Preserve input, output, cached input, reasoning output, and total tokens.
- Preserve model attribution for individual usage increments, including model changes within one thread.
- Report unknown or partial coverage when reliable attribution is impossible.
- Do not report uncertain combined totals as verified consumption.

Technical hints:

- `analytics.py`: `calculate_increments()`, `Increment`, `aggregate()`.
- Counter processing currently groups events using `event.session_id`.
- Existing counter families include `total_token_usage` and `thread_token_usage`; newer records may also expose `usage` per response.
- Review the existing parent-child overlap checks in `analytics.py` and `metrics.py`.
- Preserve existing handling of counter resets, missing values, model transitions, and cached/reasoning tokens.

### 3. Add configurable agent aggregation

Support two grouping modes across all selected conversations:

- By agent name: combine all recorded consumption under the same logical agent name, regardless of model.
- By agent name and model: separate consumption for each distinct combination.

Example:

| Agent | Model | Tokens |
|---|---|---:|
| Developer | All | 1,200,000 |
| Reviewer | All | 400,000 |

With model breakdown enabled:

| Agent | Model | Tokens |
|---|---|---:|
| Developer | Terra | 850,000 |
| Developer | Sol | 350,000 |
| Reviewer | Sol | 240,000 |
| Reviewer | Astra | 160,000 |

Use the configured agent role/name as the grouping identity where available. Do not assume that automatically generated agent nicknames identify the same logical role across conversations.

Preserve usage with unknown agent names or models in clearly identified groups. A model change must not reassign historical consumption to the latest model.

Technical hints:

- `metrics.py`: `build_dataset()`, `Filters`, `grouped()`, `summarize()`.
- Current grouping supports `project`, `model`, and `session`, but not agent name or agent-name/model combinations.
- Agent name and model should be independent grouping dimensions.
- Grouping must use attributed token records rather than only the latest agent metadata.

### 4. Update conversation and agent analytics

Update the existing dashboard to provide:

- Conversation-level statistics, including all detected related agents.
- A conversation detail view with agent hierarchy, role, model, token usage, and coverage.
- Global agent analytics independent of the selected conversation.
- A selector for grouping by agent name or agent name and model.
- Distinct agent-thread counts for each aggregated group.
- Existing date, project, model, and agent filters applied consistently.
- Readable conversation labels while preserving original identifiers.
- Clear explanations when combined totals are unavailable because counter scopes are uncertain.

Remove hardcoded subagent-share values that do not provide useful metrics. Retain independent per-agent statistics when combined totals are unavailable.

Technical hints:

- `dashboard.py`: `render()`, `details()`.
- `agents.py`: `Agent`, `AgentAnalysis`, `analyze_agents()`.
- `metrics.py`: `Metrics`, `summarize()`.
- `exports.py`: extend relevant CSV exports with conversation, thread, agent name, and model information.
- `specification/codex-usage-analyzer.md`: align the specification with the revised accounting and grouping behavior.

## Acceptance Criteria

- A conversation containing one main agent and multiple subagents is displayed as one logical conversation.
- Each agent thread is identified independently, including nested subagents.
- Unrelated conversations are not combined, even when they contain agents with identical names.
- A conversation's total usage includes independently attributable consumption from its related threads without double-counting.
- When reliable combined consumption cannot be established, the result is marked unknown or partial with an explanation.
- Per-agent token metrics remain available independently of conversation-level aggregation.
- Selecting "By agent name" combines consumption across models and conversations for the same agent name.
- Selecting "By agent name and model" produces separate entries for each distinct combination.
- An agent using two models in different conversations appears as one entry in name-only mode and two entries in name-and-model mode.
- An agent switching models within one thread has its usage attributed to the appropriate model where the source evidence supports it.
- Unknown model attribution remains visible and is not silently assigned to another model.
- Grouped totals reconcile with their underlying eligible per-thread values, subject to the same coverage and overlap rules.
- The dashboard shows the number of distinct agent threads contributing to each group.
- Conversation and agent filters produce consistent results across tables, charts, and CSV exports.
- Existing session references, manual labels, and annotations remain valid or are handled through an explicit compatibility mechanism.
- Existing supported token-accounting behavior is preserved.
- Focused static checks or existing tests cover single-agent, multi-agent, nested-agent, mixed-model, missing-metadata, and overlapping-counter scenarios without requiring full end-to-end testing.

## Dependencies

- Representative Codex JSONL records from the currently used Codex version, including main-agent and subagent activity, are needed to validate thread identity and counter scope before claiming complete conversation totals. <!-- inferred -->
- Follow the [usage rebuild and accounting rules](../specification/02-architecture/02-design/000-system-overview.md#usage-rebuild-and-accounting). Keep identity resolution and accounting callable on parsed events so [task 22](./22-build-and-report-stored-usage.md) can reuse them on collected records. Local raw collection and SQLite-backed reporting are covered by tasks 21 and 22.
