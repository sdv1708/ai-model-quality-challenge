# Issue tracker: GitHub

Issues and PRDs for this repository live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- Create issues with `gh issue create`.
- Read an issue and its discussion with `gh issue view <number> --comments`.
- List issues with `gh issue list`, including labels and comments when relevant.
- Comment with `gh issue comment <number>`.
- Apply or remove labels with `gh issue edit <number>`.
- Close completed or rejected work with `gh issue close <number>` and an explanatory comment.

Infer the repository from `git remote -v`; `gh` does this automatically when run inside this clone.

## Publishing work

When a skill says to publish a PRD or ticket to the issue tracker, create a GitHub issue in this repository.
