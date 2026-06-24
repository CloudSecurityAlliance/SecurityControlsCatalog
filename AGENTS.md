# Repository Guidelines

## Project Structure & Module Organization

The repository currently contains documentation and contribution
infrastructure; catalog content is being prepared. The root contains:

- `CLAUDE.md` / `AGENTS.md`: working context and collaboration rules (keep these two consistent).
- `README.md`: public overview of the Security Controls Catalog.
- `DESIGN-RATIONALE-STIX-EXTENSIONS.md`: draft rationale for STIX 2.1 custom SDOs and publication formats.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`: contributor docs.
- `LICENSE.txt`: CSA publication terms for the published catalog.
- `.github/`: CLA workflow, CODEOWNERS, PR and issue templates.

There are no committed source, schema, or instance-data directories yet. Before adding structure, inspect the tree (`git ls-files`) and keep proposals explicit in the pull request. Do not invent conventions for schemas, generated bundles, or instance data without maintainer agreement.

## Build, Test, and Development Commands

No build system, package manager, lint task, or automated test runner is present today.

- `git ls-files`: list tracked files quickly.
- `git status --short`: check local changes before editing or committing.
- `git log --oneline -8`: review recent commit style.

When validation tooling is introduced for STIX, OSCAL, JSON, YAML, Excel, or CSV outputs, document the exact commands here and in any related PR.

## Coding Style & Naming Conventions

Keep Markdown concise, with sentence-case prose and descriptive headings. Use fenced code blocks for examples and backticks for file names, object types, and commands. Preserve project vocabulary: CSA Security Controls Catalog (CSA-CC), STIX 2.1, OSCAL, `x-control`, `x-control-implementation`, `x-regulatory-reference`, and `x-control-assessment`.

For future structured data, prefer standard STIX 2.1 fields and relationships before adding custom `x-*` properties. Keep filenames uppercase only for top-level policy or contributor documents such as `LICENSE.txt` and `AGENTS.md`; use descriptive kebab-case for new design notes unless the repository establishes another pattern.

## Testing Guidelines

There are no tests yet. For documentation-only changes, verify Markdown renders cleanly and that links, dates, and terminology match source documents. Future schema or catalog contributions should include validator output or reproducible test commands in the PR.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects, for example `Add CLAUDE.md and STIX 2.1 design rationale`. Follow that style and add an issue or PR reference when applicable.

Use the fork-and-PR workflow; do not push directly to `main`. **Contributions require a signed Contributor License Agreement** — sign once for this project by opening a PR that adds a signature file (embedding the full CLA text) under `security-controls-catalog/signatures/` in `CloudSecurityAlliance/CLA-Ledger`; a CLA check on each PR confirms every commit author has signed for this project at the CLA version it currently requires (a material new version means re-signing); see `CONTRIBUTING.md`. PRs should explain the change, identify affected documents or future catalog artifacts, list sources for any mapping or claim, and confirm no copyrighted standard text (e.g. ISO/IEC) has been reproduced (reference standards by identifier instead).

## Security & Configuration Notes

Treat schema details as provisional unless they come from the current source-of-truth design document. Two distinct instruments govern this work: `LICENSE.txt` governs downstream consumption of the *published* catalog, while the **CLA** (not the license) governs what *contributors* grant CSA. Collaboration happens through PRs; redistribution and modification of published catalog material remain restricted under `LICENSE.txt`.
