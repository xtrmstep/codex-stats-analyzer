# 04 — Agent hierarchy, activity and skill evidence

Status: Not started | Phase: 1 | Dependencies: 02, 03

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
