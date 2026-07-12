Graphify is installed as a repository analysis skill, not MCP.

Its generated output exists in graphify-out/.

## Graphify Usage Policy
Do NOT run Graphify after every code change.
Run `graphify update .` only when:
- A feature is completed
- A sprint is completed
- Architecture changes significantly
- More than ~20 files changed
- Before requesting a repository-wide architectural analysis

For bug fixes, documentation changes, UI tweaks, or isolated edits, do not regenerate the Graphify knowledge graph.

Prefer Serena for incremental project memory.

For architectural decisions and refactors:
- read graphify-out first
- combine it with Serena symbol lookup
- use Graphify for dependency relationships
- use Serena for exact implementation details.