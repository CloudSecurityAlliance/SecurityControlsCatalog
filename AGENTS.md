# Repository Guidelines

## What This Project Is

The CSA Security Controls Catalog (CSA-CC) operates as a **subgroup of CSA's
[Compliance Automation Revolution (CAR)](https://cloudsecurityalliance.org/research/working-groups/compliance-automation-revolution)
working group**, responsible for the control layer: canonical technology-agnostic
controls and control metadata, control harmonization, regulatory mappings,
machine-readable formats, and governance of control content.

The catalog **evolves and unifies CCM and AICM** rather than standing beside them
as a third framework, and **both stay supported** — CCM has a large installed base
that will be in production for years, so CCM consumers keep a first-class
experience including their existing spreadsheet and CAIQ outputs. Forcing a CCM
migration is a design failure, not a trade-off.

The [SCC WG 2026 Charter](https://cloudsecurityalliance.org/artifacts/scc-wg-2026-charter)
sets out mission and governance, but **predates the data-format decision** — it
names a JSON/YAML schema, OSCAL, and a REST API without mentioning STIX. STIX 2.1
is the current direction and the design documents here are more current than the
charter on format; do not report the charter's silence on STIX as a finding.

## Project Structure & Module Organization

The repository currently contains documentation and contribution
infrastructure; catalog content is being prepared. The root contains:

- `CLAUDE.md` / `AGENTS.md`: working context and collaboration rules (keep these two consistent).
- `README.md`: public overview of the Security Controls Catalog.
- `DESIGN-RATIONALE-STIX-EXTENSIONS.md`: *why* STIX 2.1 — format choice and publication formats.
- `CONVENTIONS-STIX-MODELING.md`: *how* we use STIX — modeling idioms binding all objects.
- `SCHEMA-STIX-OBJECT-EXTENSIONS.md`: *what* each object carries — field-level schemas for the five custom SDOs.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`: contributor docs.
- `LICENSE.txt`: CSA publication terms for the published catalog.
- `.github/`: CLA workflow, CODEOWNERS, PR and issue templates.

`.claude/` is gitignored local working context — never quote it in a pull request, commit message, or issue.

There are no committed source, schema, or instance-data directories yet. Before adding structure, inspect the tree (`git ls-files`) and keep proposals explicit in the pull request. Do not invent conventions for schemas, generated bundles, or instance data without maintainer agreement.

## Build, Test, and Development Commands

No build system, package manager, lint task, or automated test runner is present today.

- `git ls-files`: list tracked files quickly.
- `git status --short`: check local changes before editing or committing.
- `git log --oneline -8`: review recent commit style.

When validation tooling is introduced for STIX, OSCAL, JSON, YAML, Excel, or CSV outputs, document the exact commands here, in `CLAUDE.md`, and in any related PR.

## Coding Style & Naming Conventions

**Do not restate facts that live authoritatively elsewhere.** If a fact changes
independently of this repository, link its source rather than copying its value —
what is not written down here cannot go stale here. No named individuals,
leadership lists, or role assignments in any tracked document (personnel change;
the public WG page is the source, and documents are attributed to the working
group). Likewise avoid restating version numbers or identifiers that live in
config or upstream, revision dates of documents that carry their own frontmatter
dates, and counts that shift as scope moves. Cite the location, not the content.

Keep Markdown concise, with sentence-case prose and descriptive headings. Use fenced code blocks for examples and backticks for file names, object types, and commands. Preserve project vocabulary: CSA Security Controls Catalog (CSA-CC), STIX 2.1, OSCAL, SecID, and the five object types — `x-control`, `x-regulation`, `x-control-implementation`, `x-capability`, and `x-control-assessment`.

**Before writing or generating any structured data, read the modeling conventions in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md)** — how relationships are expressed, how new object types are declared, how identifiers and SecIDs work, when a custom property is permitted, and what may be reproduced from an external source. They are not summarized here, because a second copy drifts out of step with the first. The principles behind them are defined once in [`DESIGN-RATIONALE-STIX-EXTENSIONS.md` § Design principles](DESIGN-RATIONALE-STIX-EXTENSIONS.md#design-principles).

Keep filenames uppercase only for top-level policy or contributor documents such as `LICENSE.txt` and `AGENTS.md`; use descriptive kebab-case for new design notes unless the repository establishes another pattern.

## Settled Format Questions

Decided in [`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) — read it before proposing anything about formats or publication, and reopen these only with a new technical argument:

- **STIX 2.1 is the back-end representation.** OSCAL is a *publication* format, not the back end — domain fit, no general typed-relationship primitive equivalent to a STIX SRO, and no overlap with the CTI ecosystem the catalog must join.
- **Rejected as back-end formats:** CSAF, OSV, CVE JSON, and CVRF (advisories and vulnerability records, not control catalogs), plus RDF, JSON-LD, and OWL (duplicate-purpose given SecID identity and STIX SROs).
- **Publication formats:** STIX 2.1 (primary), OSCAL, plain JSON, YAML, Excel, CSV. Excel is a first-class deliverable, not an afterthought.
- **Distribution channels:** this git repository (clone, raw URL, tagged releases) is primary; the SecID MCP server (`https://secid.cloudsecurityalliance.org/mcp`) is the AI-agent path until the CSA MCP server ships.

## Testing Guidelines

There are no tests yet. For documentation-only changes, verify Markdown renders cleanly and that links, dates, and terminology match source documents. Future schema or catalog contributions should include validator output or reproducible test commands in the PR.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects, for example `Add CLAUDE.md and STIX 2.1 design rationale`. Follow that style and add an issue or PR reference when applicable.

A **human** `Co-authored-by:` trailer requires that co-author to have signed the CLA. An **AI assistant** may be acknowledged in a trailer but is not a CLA co-author or rights-holding contributor — the committer carries responsibility for AI-assisted content. The enforced CLA version is whatever `REQUIRED_CLA_VERSION` is set to in `.github/workflows/cla.yml` — read it there rather than relying on a value quoted here.

Use the fork-and-PR workflow; do not push directly to `main`. **Contributions require a signed Contributor License Agreement** — sign once for this project by opening a PR that adds a signature file (embedding the full CLA text) under `security-controls-catalog/signatures/` in `CloudSecurityAlliance/CLA-Ledger`; a CLA check on each PR confirms every commit author has signed for this project at the CLA version it currently requires (a material new version means re-signing); see `CONTRIBUTING.md`. PRs should explain the change, identify affected documents or future catalog artifacts, list sources for any mapping or claim, and confirm no copyrighted standard text (e.g. ISO/IEC) has been reproduced (reference standards by identifier instead).

## Security & Configuration Notes

**Reference, don't reproduce.** The catalog maps to copyrighted standards. Never paste the text of an external standard into a control, mapping, or instance file — ISO/IEC text especially. Reference by identifier (clause, control, or section ID) plus original wording. This applies to generated content, not just human-authored prose.

This repository is authoritative and self-contained; there is no external design document to consult. Authority divides by question: `DESIGN-RATIONALE-STIX-EXTENSIONS.md` governs format choice and publication, `CONVENTIONS-STIX-MODELING.md` governs modeling idioms that bind all objects, and `SCHEMA-STIX-OBJECT-EXTENSIONS.md` governs field-level schemas. Each governs its own column, and where two touch the same subject the one whose column it is governs — not the more recent one. Treat all schema detail as provisional, read the documents rather than reproducing definitions from memory, and consult the **Open questions** section in both the conventions and schema documents before relying on anything they list as undecided. Two distinct instruments govern this work: `LICENSE.txt` governs downstream consumption of the *published* catalog, while the **CLA** (not the license) governs what *contributors* grant CSA. Collaboration happens through PRs; redistribution and modification of published catalog material remain restricted under `LICENSE.txt`.
