# 04 — Agent hierarchy, activity and skill evidence

Status: Implementation complete; independent review pending | Phase: 1 | Dependencies: 02, 03

Specification: §§3.2, 4.1–4.3; MVP 3, 4, 13.

## Scope

- Reconstruct main, child and nested agents from explicit identifiers and coordination events, linking associated files only when evidence supports the relationship.
- Keep unlinked agents separate. Handle missing parents, duplicate links and cycles without inventing a tree.
- Expose model, role, nickname, parent, tokens, cache percentage, first/last activity and available execution status.
- Calculate participating-agent count, maximum known hierarchy depth, main-agent tokens, combined subagent tokens and subagent share without duplicate usage.
- Build observed activity intervals and separately represent verified execution intervals. Retain evidence for overlap claims.
- Surface skill invocation evidence when available; ordinary text mentions of skills or subagents are not usage proof. Keep observed evidence separate from manual labels.

## Acceptance and validation

- Fixtures cover nested agents, unlinked agents, missing timestamps, incomplete status, cycles and parent aggregate counters.
- Conversation mentions alone create neither skill usage nor agents.
- Hierarchy metrics and token shares reconcile with task 03; missing relationships or durations remain visibly unknown.

## Decisions and validation evidence

- Each observed session/thread is an agent; explicit nested thread-spawn metadata supplies parent, role and nickname. Explicit `collab_agent_spawn` sender/receiver IDs may also establish a link. Missing parents, conflicting links, cycles and unobserved linked threads are reported without inventing agents or links. Unconnected observed threads remain separate.
- Observed first/last timestamps retain event references; only an explicit `agent_completed` record with valid start and end timestamps supplies a verified interval. Missing status and intervals remain unknown. Only explicit `skill_invoked` records with a skill name are treated as skill evidence; conversation text is not interpreted. These supported coordination and skill event shapes are conservative and were not confirmed in the sampled local files; additional formats remain unsupported.
- Per-agent token totals and cache percentages reuse task 03. Parent counters may include child usage, so main/subagent share remains unknown. Nested subagent sums are withheld when related counter streams could overlap, and missing child streams mark totals partial. Depth counts edges from the selected root; unlinked threads are excluded from its participating count.
- Inline synthetic checks passed for nested agents, unlinked and missing-parent threads, cycles, missing event timestamps, observed and verified intervals, explicit skill evidence and ignored conversation mentions. Parser and agent modules compiled. Independent review pending.


- Review fixes: resolved nested hierarchy prevents summing potentially overlapping streams even if increments lack parent IDs; explicit status and verified intervals are assigned only to a known target. Inline checks passed for both cases. Local structural inspection found `spawn_agent` results containing task names and `wait_agent` results containing timeout/message; correlated calls support plain and namespaced forms without interpreting message text. Task-name-only children remain separate from session files because no thread ID links them. Malformed arguments and incomplete results are diagnosed. Inline checks covered correlation, namespaces, unmatched outputs and timeout, and Python compilation passed. Independent re-review pending.

