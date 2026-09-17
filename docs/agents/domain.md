# Domain documentation

This repository uses a single-context domain-documentation layout.

## Before exploring

- Read `CONTEXT.md` at the repository root when it exists.
- Read relevant architectural decisions under `docs/adr/` when they exist.
- If either location does not yet exist, proceed without treating its absence as an error.

Producer workflows create domain documentation lazily as terminology and decisions are resolved.

## Vocabulary

Use the canonical terms defined in `CONTEXT.md` in issue titles, requirements, tests, architectural proposals, and implementation discussions. Avoid introducing synonyms for established concepts.

If a required concept is missing from the glossary, first determine whether it represents a genuine domain gap before adding new terminology.

## Architectural decisions

Surface conflicts with an existing ADR explicitly. Do not silently override a recorded decision.
