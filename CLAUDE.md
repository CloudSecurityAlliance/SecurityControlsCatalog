# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The working surface for the CSA **Security Controls Catalog (CSA-CC)**, which operates as a **subgroup of CSA's Compliance Automation Revolution (CAR) working group** — not a peer working group of CAR. Its remit is the control layer: a canonical set of technology-agnostic controls and control metadata, focused on control harmonization, regulatory mappings, machine-readable control formats, and governance of control content, so automation and interoperability work across CSA frameworks and external standards.

**The catalog evolves and unifies CCM and AICM** rather than standing beside them as a third framework — the CCM and AI Controls Framework working groups were consolidated into the SCC, and AICM is the starting point for v1. **Both CCM and AICM stay supported:** CCM has a large installed base that will be in production for years, and CCM consumers are expected to keep a first-class experience, including the spreadsheet and CAIQ outputs they rely on. Treat "forces CCM users to migrate" as a design failure, not a trade-off.

Reference:
- Public WG page: https://cloudsecurityalliance.org/research/working-groups/security-controls-catalog
- CAR working group: https://cloudsecurityalliance.org/research/working-groups/compliance-automation-revolution
- [SCC WG 2026 Charter](https://cloudsecurityalliance.org/artifacts/scc-wg-2026-charter)

**On the charter and STIX.** The charter predates the data-format decision. Its machine-readability objectives name a JSON/YAML schema, OSCAL integration, and a REST API, and it does not mention STIX — reading it cold, STIX looks unchartered. It isn't: STIX 2.1 is the current direction, and the design documents in this repository are more current than the charter on format. Do not raise the charter's silence on STIX as a finding. The charter also has internal inconsistencies (it refers to "CAR WG 2" and "CAR WG 3" while the public CAR page describes the SCC as a subgroup); prefer the public pages and the design documents where they diverge, and ask rather than assuming the charter is wrong.

## Repository state

This is a public CSA repository with its contribution infrastructure in place — `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, `.github/CODEOWNERS`, and the CLA-enforcement workflow (`.github/workflows/cla.yml`). Catalog content — STIX bundles and instance data — is still being prepared, so there are no committed schema or data directories yet. Do not assume directory conventions — read the current tree before writing files, and propose layout to the maintainer rather than inventing one.

Schemas are **exploratory / research status** and explicitly provisional. Do not treat any schema sketch (including the one summarized below) as normative. Always consult the in-repo design documentation (see below) before editing or generating instance data.

**Don't restate facts that live authoritatively elsewhere.** If a fact changes independently of this repository, link its source instead of copying its value — what isn't written down here can't go stale here. That covers, in particular:

- **People and their roles.** No named individuals, leadership lists, or role assignments in any tracked document. Personnel change; the public WG page is the source. Attribute documents to the working group, not to individuals.
- **Version numbers and identifiers** that live in config or upstream — the required CLA version, framework versions, endpoint URLs. Name the file or page that holds the value.
- **Revision dates** of documents that carry their own dates in frontmatter.
- **Counts** ("six working groups", "four deliverables") that shift as scope moves.

Cite the location, not the content. This applies to any document a contribution touches, not just this file.

Two tracked context files: this one and `AGENTS.md` (the generic-agent equivalent). **Keep them consistent** — a change to conventions, commands, or workflow in one belongs in the other. `.claude/` is gitignored local working context; never quote it in a PR, commit message, or issue.

## Data model (provisional)

The catalog is being designed as a graph of five custom STIX 2.1 SDO types, related via the standard STIX `relationship` SRO so the data flows unchanged through existing STIX/TAXII servers, CTI platforms, and graph stores. **The types mirror SecID's type vocabulary**, which classifies by what an artifact *is* rather than who published it:

| Object | SecID type | Role |
|---|---|---|
| `x-control` | `control` | A security control from **any** publisher — CSA, CCM, AICM, ISO 27001, NIST 800-53, CIS, PCI DSS, SOC 2 — distinguished by decomposed source-provenance properties, not by object type |
| `x-regulation` | `regulation` | A clause of legally binding law (GDPR, EU AI Act, NIS2, HIPAA). Standards are **not** regulations |
| `x-control-implementation` | — | Technology-agnostic approach to fulfilling a control ("enforce encryption at rest for object storage") |
| `x-capability` | `capability` | A specific product/service feature providing an implementation (S3 SSE-KMS, Bedrock Guardrails) |
| `x-control-assessment` | — | Outcome of a self-assessment, audit, or STAR/CAIQ evaluation |

**Superseded framework versions are carried, not deprecated.** CCM 4.0 and 4.1 coexist as `x-control` objects distinguished by `framework_version`, related by `maps-to`. Organizations stay certified against earlier editions for years and much existing mapping work targets them, so dropping a version because a newer one exists would remove coverage people depend on. See the version-coverage principle in the rationale.

The layers change on different timescales — controls are stable for years, implementation approaches change with architecture, capabilities change whenever a vendor ships — which is why they are separate objects. SecID's `reference` and `methodology` types are **not** modeled as objects; they are cited via `external_references`.

**This repository is authoritative and self-contained.** There is no external design document to consult and none to ask for access to. Three in-repo documents divide the design by the question they answer:

| Question | Document | Authority over |
|---|---|---|
| **Why** | [`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) | Format choice, publication formats, distribution channels |
| **How** | [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md) | Modeling idioms binding all objects — relationships, identifiers, custom-property discipline |
| **What** | [`SCHEMA-STIX-OBJECT-EXTENSIONS.md`](SCHEMA-STIX-OBJECT-EXTENSIONS.md) | Field-level schemas — the properties of each SDO |

Each document governs its own column: the rationale settles format and publication, the conventions settle modeling idioms, the schema settles fields. Where two documents touch the same subject, the one whose column it is governs — not the newer one. Never reproduce field definitions from memory or infer them from other STIX extensions — read the schema document. **Both the conventions and schema documents carry an `Open questions` section listing what is genuinely undecided** — read those sections rather than a summary here, which would go stale as questions get settled. Raise an issue rather than inventing an answer to any of them in instance data.

Objects carry a [SecID](https://secid.cloudsecurityalliance.org/) (for example `secid:control/cloudsecurityalliance.org/ccm@4.1#CEK-03`) so they resolve through SecID's public resolver. A SecID does **not** go in the STIX `id` property: STIX 2.1 requires `id` to be `<type>--<UUIDv4>`, so a `secid:` URI there is invalid STIX and breaks the maximum-compatibility principle. Carry it in `external_references`, and decompose its components into queryable properties for third-party content. Do not invent a third identifier scheme.

## Load-bearing design principles and conventions

**Read these before proposing or generating anything about the data model.** Violating one is a category error, not a style nit. They are deliberately **not** listed or summarized here — a list of what those documents contain goes stale the moment one is added, renamed, or settled, which has already happened once:

- **Design principles** — [`DESIGN-RATIONALE-STIX-EXTENSIONS.md` § Design principles](DESIGN-RATIONALE-STIX-EXTENSIONS.md#design-principles), their single home.
- **Modeling conventions** — [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md), numbered sections plus an `Open questions` list.

The distinction is worth keeping straight: principles are *why* the design is shaped as it is and change rarely; conventions are *how* to model something and are where the operative rules live.

## Settled questions — do not re-litigate

Decided in the design rationale; reopen only with a new technical argument:

- **STIX 2.1 is the back-end representation.** OSCAL is a *publication* format, not the back end — domain fit, no general typed-relationship primitive equivalent to a STIX SRO, and no overlap with the CTI ecosystem the catalog must join.
- **Rejected as back-end formats:** CSAF, OSV, CVE JSON, and CVRF (all wrong domain — advisories and vulnerability records, not control catalogs), plus RDF, JSON-LD, and OWL (duplicate-purpose given SecID identity and STIX SROs).
- **Publication formats:** STIX 2.1 (primary), OSCAL, plain JSON, YAML, Excel, CSV. Excel is a first-class deliverable — the CCM customer base has consumed spreadsheet exports for over a decade.
- **Distribution channels:** this git repository (clone, raw URL, tagged releases) is primary; the SecID MCP server (`https://secid.cloudsecurityalliance.org/mcp`) is the AI-agent path until the CSA MCP server ships.

## Hard content constraint: reference, don't reproduce

The catalog maps to copyrighted standards. **Never paste the text of an external standard** into a control, mapping, or instance file — ISO/IEC text especially. Reference by identifier (clause, control, or section ID) plus original wording. This applies to generated content, not just human-authored prose.

## Adjacent ecosystems CSA-CC must interoperate with

When making design or mapping decisions, keep these in scope:

- **CSA frameworks and artifacts**: CCM, AICM, IoT security initiatives, STAR/CAIQ, *Top Threats to Cloud Computing* annual report (controls should be expressible as "mitigates threat X" against the current threat list)
- **Standards**: STIX 2.1, OSCAL, MITRE ATT&CK (via `attack-pattern`)
- **External frameworks and law**: other publishers' controls (ISO 27001, NIST 800-53, CIS, PCI DSS) are `x-control` objects; binding law (GDPR, EU AI Act, HIPAA) is `x-regulation`. Do not file a standard as a regulation.

## Workflow

This is a public CSA repository. External collaboration uses the standard fork + PR model. Do not push directly to `main`; create a branch and open a PR for any change.

**Contributions require a signed Contributor License Agreement (CLA).** See `CONTRIBUTING.md` for the contributor flow and what signing means. To sign, a contributor opens a PR adding a signature file — named for their numeric GitHub account ID and embedding the full CLA text — under `security-controls-catalog/signatures/` in the public `CloudSecurityAlliance/CLA-Ledger` repository; CSA accepts by merging. Coverage is **per project**: a contributor signs once for this project and signs other CSA projects' CLAs separately. The CLA check in `.github/workflows/cla.yml` verifies, on each PR, that every commit author has a signature for this project **at the CLA version the project currently requires** in the ledger (a material new version means re-signing; it reads the public ledger directly — no bot, no token). `main` is branch-protected: PRs require a passing CLA check, a review, and — for `LICENSE.txt` and `.github/` — a CODEOWNERS review.

The rationale behind the CLA design — forward-looking scope, the commit-author check, reviewed signature PRs, `pull_request_target` safety, and more — is documented in the CLA-Ledger's [`DESIGN-NOTES.md`](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/DESIGN-NOTES.md). Consult it before treating a CLA design choice as an oversight.

Commits use short imperative subjects (for example `Add CLAUDE.md and STIX 2.1 design rationale`). A PR should explain the change, list the sources behind any mapping or claim, and confirm no copyrighted standard text was reproduced. A **human** `Co-authored-by:` trailer requires that co-author to have signed the CLA; an **AI assistant** may be acknowledged in a trailer but is not a CLA co-author or rights-holding contributor — the committer carries responsibility for AI-assisted content. The enforced version is whatever `REQUIRED_CLA_VERSION` is set to in `.github/workflows/cla.yml` — read it there rather than relying on a value quoted here.

The `LICENSE.txt` reflects CSA's standard publication terms (no modification or redistribution of the *published* catalog). It governs downstream consumption of releases, not the development process; the **CLA**, not the license, governs what contributors grant CSA. Treat these as two distinct instruments.

## Build / lint / test

None yet — no package manager, linter, or test runner. Orientation commands:

```sh
git ls-files          # full tracked tree (do not assume directory conventions)
git log --oneline -8  # commit style
```

When schema validation, OSCAL conversion, or STIX bundle generation tooling is added, document the exact commands here **and in `AGENTS.md`**.
