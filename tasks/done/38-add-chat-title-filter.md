## Title

Filter Overview usage by chat title

## Dependencies

Task 37 provides the name-based Agent selector and the shared execution-ID filter path. The imported root-derived titles from completed task 34 provide the Chat option labels.

## Specification

Follow the [Chat and Agent filter behavior](../specification/01-screens/010-navigation.md#15-filters).

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), add **Chat** above **Agent** in the Overview Filters section. Build distinct non-empty title options from the eligible `report_calculator.threads` using `chat_title`. Sort options by title for browsing. Use a separate internal value for **All chats**. Use the exact imported title for matching, including when several verified roots have the same title. Keep unknown titles in the unrestricted path.
- Apply the selected title to the eligible threads before constructing Agent options. An unavailable Chat selection resets to **All chats**. Keep the Agent name when it is still available in the narrowed list and reset it to **All agents** otherwise. Resolve the intersection to execution IDs and reuse task 37's path into `StatsRequest.agents` and the observed-event frame. With a specific title and **All agents**, pass the IDs for every eligible execution with that title. With both selectors unrestricted, retain all records allowed by the other filters.
- Reuse `chat_title` from the committed thread snapshot in [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py). The importer already propagates the root title through verified ancestry in [`transformations.py`](../src/internal/ingestion/transformations.py). Leave source import, storage, project attribution, and accounting as they are. Keep chat titles as filter labels and preserve existing chart groups and CSV columns.

## Acceptance Criteria

- **Chat** displays only known titles and **All chats**. Selecting a title includes matching roots and their verified subagents, including descendants recorded with different source session IDs. When two roots have the same title, the one title option includes both. Untitled and unattributed usage remains available with both selectors unrestricted.
- Selecting a Chat narrows Agent options. A name common to two chats can be used across both under **All chats**, or within the selected title. A previously selected name that is unavailable under the new Chat returns to **All agents**.
- Chat, Agent, and the other existing filters intersect consistently in **Full selected period**, **Since [marker]**, and the usage CSV. Manual annotations and project and model grouping behave as before.
