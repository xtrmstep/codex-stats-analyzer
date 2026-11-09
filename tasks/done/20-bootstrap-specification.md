# Task: Bootstrap and Standardize the System Specification

## 1. Objective
Create a consistent, maintainable specification structure under `specification/` that serves as the **single source of truth for the intended system** and guides AI coding agents through implementation and future specification changes.

The specification must be readable by both humans and AI agents, support navigation through numbered documents and cross-references, and provide clear engineering and documentation conventions.

This task establishes the **specification framework**, not the actual system design or functionality.

The result should be minimal but sufficiently detailed to guide agents consistently.

## 2. Scope
The task covers:

1. Creating or organizing the specification directory structure.
2. Establishing `specification/AGENTS.md` as the single entry point.
3. Creating standard engineering guidelines.
4. Establishing rules for architecture diagrams and design documentation.
5. Establishing rules for organizing UI screen specifications.
6. Establishing conventions for API and data contracts.
7. Defining document numbering, references, and maintenance rules.
8. Preserving existing specifications while integrating them into the new structure where applicable.

**Out of scope:**

- Implementing or refactoring application code.
- Designing system-specific classes, components, or workflows.
- Creating actual UI screen specifications unless existing documents need to be organized.
- Inventing API contracts or data schemas.
- Introducing new testing frameworks or automated test suites.
- Large-scale documentation rewriting unrelated to this structure.

## 3. Preparation and Repository Inspection
Before making changes:

1. Read the repository's root `AGENTS.md`, if present.
2. Inspect the current `specification/` directory and its existing organization.
3. Identify existing engineering guidelines, screens, diagrams, contracts, and related documentation.
4. Check for existing references between specification documents.
5. Identify any ongoing specification restructuring and preserve its current intent.
6. Review repository conventions and languages so the new guidelines do not contradict established technical requirements.

Do not assume that the repository matches an older structure.

Preserve existing specification content and avoid overwriting or deleting documents without understanding their purpose.

Where existing documents already cover the proposed guidelines, reuse or reorganize them instead of creating duplicate content.

## 4. Target Directory Structure
Use the following structure as the baseline:

```
specification/
├── AGENTS.md
│
├── 01-screens/
│   ├── AGENTS.md
│   ├── 000-main-layout.md
│   ├── 010-<screen-or-element>.md
│   └── ...
│
├── 02-architecture/
│   ├── 01-guidelines/
│   │   ├── 010-engineering-principles.md
│   │   ├── 020-naming-conventions.md
│   │   ├── 030-code-style.md
│   │   ├── 040-verification.md
│   │   └── 050-diagram-guidelines.md
│   │
│   └── 02-design/
│       └── (reserved for future design documents)
│
└── 03-contracts/
    └── AGENTS.md
```

Screen specification documents live directly in `01-screens/` without an application subdirectory unless multiple distinct applications require separation. The illustrative screen documents (`000-main-layout.md`, `010-...`) show the naming pattern only.

The design directory must remain a placeholder until actual design requirements are available. If an empty directory must be tracked by Git, use a minimal `.gitkeep` file.

Create `api/`, `schemas/`, and `events/` under `03-contracts/` only when they contain actual contracts or are already used by the repository. Avoid unnecessary empty directories.

## 5. Specification Entry Point — `specification/AGENTS.md`
Create or update `specification/AGENTS.md`.

This must be the **single entry point for both humans and AI agents**. Do not create a separate specification `README.md`.

Keep it compact, concise, and readable. Detailed conventions belong in the relevant guideline documents.

### Required content

**Purpose**

Explain that the specification defines intended system behavior, architecture, and interfaces and serves as the authoritative reference for implementation.

**Structure**

Provide a short directory map explaining the responsibility of each specification area.

**Navigation**

- Start with documents relevant to the assigned task.
- Follow references to related specifications.
- Consult applicable engineering guidelines.
- Avoid unnecessary exploration of unrelated areas.

**Document conventions**

- Use three-digit prefixes for document ordering.
- Use increments of ten by default.
- Preserve existing document numbers and filenames where possible.
- Use relative Markdown links for cross-references.
- Keep each requirement or decision in one authoritative location.
- Prefer references over duplication.

**Agent workflow**

- Read relevant specifications before implementation.
- Follow applicable engineering conventions.
- Implement the smallest change satisfying the specification.
- Review related specifications when changing a document.
- Keep specification-only changes separate from implementation changes.
- Verify relevant changes.
- Report contradictions, missing requirements, and differences between specification and implementation.

### Additional requirements

- The specification describes the intended target system, not necessarily the current implementation.
- Existing code must not silently override the specification.
- Agents must not modify unrelated implementation code while updating specifications.
- If the repository has a root `AGENTS.md`, ensure agents can discover the specification entry point without duplicating its instructions.

## 6. Architecture Guidelines
Create the following documents under:

`specification/02-architecture/01-guidelines/`

These documents provide reusable engineering conventions applicable to the repository.

Guidelines should distinguish mandatory rules from recommendations requiring engineering judgment.

### 6.1. `010-engineering-principles.md`
Define the general engineering philosophy.

Include the following principles:

**First-principles thinking**

- Understand the actual requirements before designing a solution.
- Challenge unnecessary assumptions.
- Solve the underlying problem rather than automatically preserving historical complexity.

**Simplicity**

- Prefer the simplest solution that fully satisfies the requirements.
- Follow KISS and YAGNI.
- Avoid premature abstractions, unnecessary extensibility, and speculative functionality.
- Do not introduce additional layers, classes, or interfaces without clear justification.

**SOLID**

- Apply SOLID principles where they improve maintainability.
- Prefer clear responsibilities and explicit dependencies.
- Do not apply SOLID mechanically when doing so increases complexity without practical benefit.

**DRY**

- Avoid unnecessary duplication of logic.
- Do not introduce abstractions solely to eliminate small, incidental repetition.
- Favor readable, locally understandable code over excessive reuse.

**Minimal changes**

- Make the smallest meaningful change needed to meet the requirements.
- Preserve existing behavior outside the requested scope.
- Avoid unrelated cleanup, restructuring, and refactoring.
- Follow existing conventions unless a change explicitly requires otherwise.

**Maintainability**

- Prioritize correctness, readability, and ease of modification.
- Prefer understandable solutions over technically elaborate ones.
- Keep dependencies and interactions explicit.
- Use established project technologies before introducing new dependencies.

State the intended priority order:

1. Correctness and specification compliance.
2. Simplicity and readability.
3. Maintainability.
4. Minimal scope of changes.
5. Reuse and abstraction when justified.

The principles must be pragmatic rather than rigid architectural dogma.

### 6.2. `020-naming-conventions.md`
Define consistent naming expectations.

Cover:

- Classes and interfaces.
- Methods and functions.
- Variables and parameters.
- Constants.
- Modules, packages, and source files.
- Public and private identifiers.
- Abbreviations and acronyms.

General rules:

- Names must communicate purpose clearly.
- Prefer descriptive but concise names.
- Avoid misleading or excessively generic names.
- Use terminology consistently across related components.
- Follow the standard conventions of the language and framework.
- Avoid creating new naming schemes when repository conventions already exist.
- Distinguish interfaces, implementations, and responsibilities through meaningful names rather than arbitrary prefixes.

Inspect the programming languages used by the repository and document relevant conventions.

Do not introduce conventions for technologies that the project does not use.

### 6.3. `030-code-style.md`
Define general coding and documentation rules.

Include:

**Code organization**

- Prefer small, focused classes and functions.
- Maintain clear separation of responsibilities.
- Avoid excessive nesting and unnecessary indirection.
- Prefer composition and explicit dependencies where appropriate.
- Follow established repository formatting and coding conventions.

**Comments and documentation**

- Use Google-style docstrings for Python where documentation is needed.
- Follow equivalent established conventions for other languages.
- Document public interfaces and non-obvious behavior when useful.
- Explain intent, reasoning, and important constraints.
- Avoid comments that merely repeat what the code already expresses.
- Avoid verbose documentation for trivial or self-explanatory implementation details.
- Keep documentation synchronized with behavior.

**Implementation discipline**

- Avoid unnecessary dependencies and abstractions.
- Do not introduce unrelated refactoring.
- Maintain compatibility with existing interfaces unless explicitly changed.
- Prefer clear code over clever or highly compressed expressions.

Keep the document technology-aware but avoid duplicating official language style guides.

### 6.4. `040-verification.md`
Define how agents should verify implementation and specification changes.

**Current project policy: unit tests are not required.**

Do not introduce new unit tests or test infrastructure unless explicitly requested.

Existing tests must not be removed or deliberately broken.

**Required verification approach**

Use appropriate checks based on the change:

- Syntax and compilation checks.
- Static analysis and linting where tools exist.
- Type checking where configured.
- LLM-assisted analysis of correctness, consistency, and specification compliance.
- Review of affected interfaces, dependencies, and contracts.
- Targeted execution or integration checks when necessary and feasible.

For documentation-only changes:

- Check Markdown structure and readability.
- Check relative links and references.
- Check numbering conventions.
- Check consistency with related specifications.
- Check that no existing requirements have been unintentionally removed.

Explicitly acknowledge that static analysis and LLM review do not guarantee runtime correctness.

Agents must report which checks were performed and identify checks that could not be performed.

Do not require installing new verification frameworks or introducing unnecessary tools.

### 6.5. `050-diagram-guidelines.md`
Define rules for future architecture diagrams without creating system-specific diagrams.

**General conventions**

- Use Mermaid embedded in Markdown as the default diagram format.
- Keep diagrams readable and focused on a specific architectural concern.
- Show important relationships without reproducing all implementation details.
- Use consistent names and terminology.
- Keep diagrams aligned with the accompanying textual specification.
- Prefer multiple focused diagrams over one overloaded diagram.
- Do not duplicate information unnecessarily between diagrams.

**System overview diagrams**

- Show major subsystems, boundaries, and external dependencies.
- Focus on the overall organization of the system.
- Exclude low-level classes and implementation details.

**Component diagrams**

- Show major components, responsibilities, dependencies, and interfaces.
- Make communication direction explicit when relevant.
- Group components according to meaningful system boundaries.

**Class diagrams**

- Include important classes and interfaces.
- Show significant inheritance, composition, and dependencies.
- Focus on responsibilities and public relationships.
- Avoid documenting every method, field, or helper class.
- Do not automatically generate large class diagrams from the entire codebase.

**Flowcharts**

- Describe significant processing steps and decisions.
- Make branching conditions understandable.
- Include relevant error handling or failure paths.
- Avoid unnecessary low-level implementation steps.

**Sequence diagrams**

- Describe important interactions between components over time.
- Identify participants clearly.
- Show significant requests, responses, and asynchronous interactions.
- Avoid excessive detail.

**Organization**

- Store actual system design documents under `02-architecture/02-design/`.
- Use numbered documents and relative references.
- Introduce `000-system-overview.md` when the system-level architecture is first defined.
- Add dedicated design documents only when necessary.

Do not create empty diagram templates or speculative architecture documents.

## 7. Screen Specification Guidelines
Create:

`specification/01-screens/AGENTS.md`

This document defines how user interfaces should be described and how screen specifications should be organized.

### 7.1. General approach
Screen specifications describe **what users see and how the interface behaves**.

They must be sufficiently precise for an implementation agent to reproduce the intended user experience without inventing significant behavior.

They should avoid unnecessary internal implementation details.

### 7.2. Organization

- Organize screens by application or UI area.
- Place screen documents directly in `01-screens/` unless multiple distinct applications require a subdirectory.
- Start with `000-main-layout.md` where a top-level page layout is needed.
- Use subsequent documents for significant screens, sections, or complex UI elements.
- Keep numbering stable when inserting new documents.
- Use relative references between parent screens and detailed element specifications.

### 7.3. Main layout document
The main layout document should describe:

- Overall page structure.
- Main visible sections.
- General positioning and hierarchy.
- Navigation between areas.
- Important shared controls.
- Initial or empty state where applicable.
- References to separate specifications for complex elements.

A main layout should allow an agent to understand how the page is composed without reading every detailed interaction specification.

### 7.4. Rules for splitting documents
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

### 7.5. Screen document content
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

### 7.6. Visual representation

- Use concise descriptions for straightforward layouts.
- Allow simple Markdown or ASCII sketches when helpful.
- Use Mermaid diagrams for interactions or flows where appropriate.
- Keep visual representations consistent with the written requirements.
- Avoid requiring screenshots, design tools, or complex visual documentation for simple screens.

### 7.7. Boundaries
Screens define observable behavior.

Architecture defines internal components and implementation responsibilities.

Contracts define interface structures and validation.

Reference architecture and contract documents instead of duplicating their content in screen specifications.

### 7.8. Extending screen specifications
When adding or changing a screen:

1. Find the applicable parent screen or layout.
2. Decide whether the change belongs in the existing document or needs a separate document.
3. Preserve existing requirements unless explicitly changed.
4. Update the parent layout when the overall composition changes.
5. Add or update references to related specifications.
6. Review relevant contracts and architectural implications.
7. Keep changes focused on the affected UI area.

## 8. Contract Specification Guidelines
Create:

`specification/03-contracts/AGENTS.md`

Define how interfaces between system components should be specified.

### Purpose
Contracts define agreed interfaces and data structures between components, applications, or external systems.

Examples include frontend/backend communication, service APIs, events, and shared configuration schemas.

### Contract organization

- `api/` — HTTP APIs and other service interface definitions.
- `schemas/` — shared data structures and configuration schemas.
- `events/` — event and message contracts.

Create these subdirectories only when they contain actual contracts. Avoid empty placeholder directories.

Additional categories may be introduced when justified.

### Format conventions

- Prefer OpenAPI for HTTP API definitions.
- Prefer JSON Schema for JSON-based data structures.
- Use appropriate machine-readable formats for event contracts when applicable.
- Use Markdown for explanations that cannot be expressed clearly in the contract definition.

### Required contract qualities
Contracts should explicitly define applicable:

- Field names and data types.
- Required and optional fields.
- Validation constraints.
- Request and response structures.
- Error representations.
- Compatibility requirements.
- Event or message semantics.

### General rules

- Keep contracts independent from internal implementation classes.
- Reuse shared schemas when they represent the same concept.
- Avoid unnecessary duplication.
- Keep producer and consumer expectations consistent.
- Do not silently introduce breaking interface changes.
- Reference contracts from screens and architecture documents when applicable.
- Preserve existing contract identifiers and filenames when changing them would break references or consumers.

Do not create speculative API definitions or schema examples.

## 9. Document Numbering and Cross-References
Establish the following common conventions across the specification.

### Numbering

- Use three-digit numeric prefixes for Markdown specification documents.
- Start with `000` for an overview or primary layout where applicable.
- Use increments of ten for normal document ordering.
- Allow intermediate numbers, such as `015`, when adding documents between existing ones.
- Preserve stable filenames and numbers when possible.
- Numbering determines document order, not implementation priority.
- Each directory that serves as a specification area entry point uses `AGENTS.md` as its guidelines or conventions document, without a numeric prefix.

### References

- Use relative Markdown links.
- Reference related specifications rather than repeating their content.
- Include parent-child references where they improve navigation.
- Ensure referenced paths exist.
- Update affected references when moving or renaming documents.

### Single source of truth
Each requirement, engineering convention, contract, or design decision should have one authoritative location.

Other documents may summarize its purpose but should link to its authoritative definition rather than duplicating detailed rules.

### Document maintenance
When changing a specification:

1. Identify the authoritative document.
2. Find related references and dependent specifications.
3. Update the smallest set of affected documents.
4. Preserve unrelated requirements.
5. Verify references and consistency.
6. Report implementation gaps caused by the change.

Avoid introducing separate metadata files, document registries, global IDs, or dependency-tracking mechanisms unless a real requirement makes them necessary.

## 10. Handling Existing Specifications
The repository may already contain screens, architecture documents, components, workflows, or other specification materials.

The agent must:

1. Inspect existing files before reorganizing.
2. Identify which existing documents fit the target structure.
3. Preserve meaningful content and requirements.
4. Avoid duplicate authoritative documents.
5. Update references affected by necessary moves.
6. Avoid renaming unrelated files simply to satisfy cosmetic conventions.
7. Avoid inventing new system requirements during migration.

If existing documentation describes system functionality that does not fit naturally into screens, architecture, or contracts, preserve it and report the organizational question rather than forcing it into an unsuitable category.

Do not expand this task into a complete specification redesign.

## 11. Implementation Constraints

- Work primarily within `specification/`.
- Modify root `AGENTS.md` only if necessary to make the specification discoverable.
- Do not change application source code.
- Do not introduce new dependencies or tools.
- Do not add unit tests.
- Do not create a separate specification `README.md`.
- Do not create fictional system diagrams, screens, or contracts.
- Do not duplicate instructions across multiple files.
- Avoid excessive templates, metadata, and documentation bureaucracy.
- Prefer the smallest number of focused documents that fully cover the agreed conventions.

## 12. Acceptance Criteria

### Structure

- `specification/AGENTS.md` is the single human/agent entry point.
- The agreed screens, architecture, and contracts organization exists.
- All five engineering guideline documents are present under `02-architecture/01-guidelines/`.
- `specification/01-screens/AGENTS.md` contains screen organization guidelines.
- `specification/03-contracts/AGENTS.md` contains contract guidelines.
- The architecture design area is reserved without invented designs.
- No redundant specification `README.md` is introduced.

### Content

- Engineering principles cover SOLID, DRY, first principles, KISS, YAGNI, simplicity, and minimal changes.
- Naming conventions are consistent with repository languages and conventions.
- Code style establishes Google-style Python docstrings and concise commenting practices.
- Verification guidelines define static analysis, LLM review, and the policy of not requiring unit tests.
- Diagram guidelines cover system overview, component, class, flowchart, and sequence diagrams.
- Screen guidelines explain layout descriptions, states, interactions, and when to split documents.
- Contract guidelines define organization, preferred formats, interface expectations, and compatibility principles.
- General instructions describe implementation and specification-change workflows.

### Consistency

- Documents use consistent numbering and naming.
- Entry-point and guidelines documents at each specification area use the `AGENTS.md` filename.
- Relative Markdown links resolve correctly.
- Detailed rules are not duplicated unnecessarily.
- Existing requirements are preserved.
- No conflicting rules are introduced.
- Existing unrelated application files remain unchanged.

### Quality

- Documents are concise and readable by humans.
- Instructions are sufficiently explicit for AI agents.
- No unnecessary examples, placeholders, or speculative designs are introduced.
- The structure can be extended without reorganizing the entire specification.

## 13. Verification
Perform the following checks:

1. Inspect the final specification directory tree.
2. Verify the existence of all required documents.
3. Validate relative Markdown references.
4. Check document numbering and naming consistency, including `AGENTS.md` usage.
5. Review guidelines for contradictions and duplicated requirements.
6. Compare moved or reorganized existing documents to ensure requirements were not lost.
7. Review the specification from an AI agent's perspective: verify that it is clear where to find requirements, how to interpret them, and how to handle changes.
8. Review readability from a human perspective: verify that `AGENTS.md` provides enough context to navigate the structure without additional entry-point documentation.

No application execution or unit tests are required for this documentation task.

## 14. Expected Deliverables
Provide:

1. The created or updated `specification/` structure.
2. All agreed guideline documents with substantive content.
3. The compact `specification/AGENTS.md`.
4. Updated references for any reorganized existing documents.
5. A concise completion report containing:
   - Documents created or modified.
   - Existing documents reorganized, if any.
   - Verification performed.
   - Unresolved inconsistencies or organizational questions.

**Completion principle:** Establish a practical, consistent specification foundation that can guide AI-assisted development immediately, without prematurely designing the system or introducing unnecessary documentation complexity.
