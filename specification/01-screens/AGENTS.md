# Screen Specification Guidelines

This document defines how user interfaces should be described and how screen specifications should be organized.

## Purpose

Screen specifications describe what users see and how the interface behaves. They must be sufficiently precise for an implementation agent to reproduce the intended user experience without inventing significant behavior. They avoid unnecessary internal implementation details.

## Organization

- Organize screens by application or UI area.
- Use numbered Markdown documents within each application directory.
- Start with `000-main-layout.md` where a top-level page layout is needed.
- Use subsequent documents for significant screens, sections, or complex UI elements.
- Keep numbering stable when inserting new documents.
- Use relative references between parent screens and detailed element specifications.

## Main layout document

The main layout document should describe:

- Overall page structure.
- Main visible sections.
- General positioning and hierarchy.
- Navigation between areas.
- Important shared controls.
- Initial or empty state where applicable.
- References to separate specifications for complex elements.

A main layout should allow an agent to understand how the page is composed without reading every detailed interaction specification.

## When to split documents

**Create a separate document when:**

- A new independently navigable page is introduced.
- A UI section has substantial independent behavior.
- An element has multiple meaningful states or interactions.
- A complex configuration form requires detailed explanation.
- A shared UI element is used in multiple screens and has substantial behavior.
- A document becomes too large or mixes several independent concerns.

**Keep elements in the parent document when:**

- They are simple labels, buttons, or inputs.
- Their behavior can be clearly described in a few sentences.
- They do not have significant independent state or interaction rules.
- Separating them would increase navigation overhead without adding clarity.

Do not automatically create one document per UI component.

## Screen document content

Include the applicable information:

- Purpose of the screen or element.
- Visible layout and structure.
- UI elements and their roles.
- Initial, empty, loading, success, and error states where relevant.
- User interactions and expected outcomes.
- Validation and feedback behavior.
- Navigation behavior.
- References to related screens and contracts.

Do not require empty sections when they are not relevant.

## Visual representation

- Use concise descriptions for straightforward layouts.
- Allow simple Markdown or ASCII sketches when helpful.
- Use Mermaid diagrams for interactions or flows where appropriate.
- Keep visual representations consistent with the written requirements.
- Avoid requiring screenshots, design tools, or complex visual documentation for simple screens.

## Boundaries

- Screens define observable behavior.
- Architecture defines internal components and implementation responsibilities.
- Contracts define interface structures and validation.

Reference architecture and contract documents instead of duplicating their content in screen specifications.

## Extending screen specifications

When adding or changing a screen:

1. Find the applicable parent screen or layout.
2. Decide whether the change belongs in the existing document or needs a separate document.
3. Preserve existing requirements unless explicitly changed.
4. Update the parent layout when the overall composition changes.
5. Add or update references to related specifications.
6. Review relevant contracts and architectural implications.
7. Keep changes focused on the affected UI area.
