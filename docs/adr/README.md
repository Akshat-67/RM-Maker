# Architecture Decision Records (ADRs)

An Architecture Decision Record (ADR) is a document that captures a significant design or architectural choice made in this project, including its context, decision rationale, alternatives considered, and consequences.

---

## Why Use ADRs?
Code alone shows *what* was built, but it rarely explains *why*. Future engineers and AI agents require access to the historical context and design reasoning to:
- Avoid re-introducing legacy bugs.
- Respect intentional design boundaries.
- Understand the tradeoffs accepted during development.

---

## When to Create an ADR
Create a new ADR whenever you:
- Introduce a new framework, package, or pipeline.
- Modify the project's data schema contracts or storage strategies.
- Alter the separation of concerns between core layers (e.g. front-end vs back-end, template vs extraction).
- Overhaul core algorithms or infrastructure configurations.

---

## Naming & File Conventions
All ADRs reside in the `docs/adr/` directory and use the following naming convention:
- **Format**: `ADR-XXXX.md` (where `XXXX` is a sequential 4-digit number starting at `0001`).
- **Index**: Maintain references to all active, proposed, or superseded decisions in the table below.

---

## Decision Status Definitions
- **Proposed**: The decision is drafted and under active review.
- **Accepted**: The decision has been approved and implemented in the codebase.
- **Superseded**: A newer decision (`ADR-YYYY`) has replaced this choice.
- **Deprecated**: The decision is no longer relevant or active.

---

## ADR Index

| ID | Title | Status | Date |
| :--- | :--- | :--- | :--- |
| [ADR-0001](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0001.md) | Unicode as Canonical Representation | Accepted | 19-07-2026 |
| [ADR-0002](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0002.md) | DevLys Rendering Boundary | Accepted | 19-07-2026 |
| [ADR-0003](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0003.md) | RM and SD Independent Pipelines | Accepted | 19-07-2026 |
| [ADR-0004](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0004.md) | AI Extracts Facts, Templates Own Legal Language | Accepted | 19-07-2026 |
| [ADR-0005](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0005.md) | Removal of Graphify | Accepted | 19-07-2026 |
| [ADR-0006](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0006.md) | Runtime Data is Not Source Code | Accepted | 19-07-2026 |
| [ADR-0007](file:///c:/Users/aksha/Documents/RM%20Generator/RM-Maker/RM-Maker-MAIN/docs/adr/ADR-0007.md) | Incremental Refactoring Policy | Accepted | 19-07-2026 |

---

## ADR Template
Future ADR files must follow this exact format:

```markdown
# ADR-XXXX: [Title]

## Status
[Proposed | Accepted | Superseded by ADR-YYYY | Deprecated]

## Date
[DD-MM-YYYY]

## Context
Provide the problem description, user requirements, technical pain points, or constraints that prompted this decision.

## Decision
Detail the chosen path, the technical implementation rules, and why this alternative was selected.

## Alternatives Considered
List other solutions evaluated and explain why they were rejected.

## Consequences
Describe the results of this choice:
- **Positive**: What is easier, safer, or more performant now?
- **Negative/Neutral**: What overhead, limitations, or trade-offs were accepted?

## Future Considerations
Mention potential long-term impacts, scaling metrics, or scenarios that might warrant revisiting this decision.
```
