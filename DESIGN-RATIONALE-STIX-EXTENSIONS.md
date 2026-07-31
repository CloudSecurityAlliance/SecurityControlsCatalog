---
title: "CSA Security Controls Catalog — Design Rationale: STIX 2.1 Extensions"
document-status: DRAFT
date: 2026-05-07
author: "CSA Security Controls Catalog working group, with AI assistance"
status: "Provisional — open for discussion"
type: "Design rationale"
tags: [security-controls-catalog, stix, oscal, format, design-rationale]
---

# CSA Security Controls Catalog — Design Rationale: STIX 2.1 Extensions

## 1. Purpose and scope

This document outlines the technical rationale behind the format and distribution choices proposed for the CSA Security Controls Catalog ([CloudSecurityAlliance/SecurityControlsCatalog](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog)). It addresses three questions:

1. Why STIX 2.1 with custom STIX Domain Object (SDO) extensions as the back-end representation?
2. Why not OSCAL — or CSAF, OSV, RDF, or a purpose-built custom format?
3. What formats and channels should the catalog be published through?

The arguments here are technical. Specific deliverables, sequencing, and governance are out of scope.

The catalog's data model is exploratory and research-grade. Schemas described in this document are provisional and may evolve as implementation experience accumulates.

### Design principles

These are the principles the catalog's design answers to, and that contributions must respect — violating one is a category error rather than a style nit. **This section is the single home for them**; the other design documents and the repository's context files point here rather than restating them.

- **Minimal invention.** Introduce new object types or properties only where CSA-CC concepts cannot reasonably be expressed with existing STIX 2.1 objects, vocabularies, or relationships. Standard STIX is preferred over bespoke structures, even at the cost of some CSA-specific convenience.
- **Alignment over replacement.** This work does not replace existing control-modeling efforts — OSCAL in particular — and is not a universal GRC schema. It is an interoperability layer. Do not propose designs that compete with OSCAL; propose ones that interoperate with it.
- **Maximum compatibility with existing tools.** Catalog objects are valid STIX 2.1 and are intended to flow unchanged through existing STIX/TAXII servers, CTI platforms, graph databases, and analysis pipelines. Nothing changes the STIX wire format, versioning model, or transport. If a design would require a consumer to special-case the catalog before it can parse or route the data, the design is wrong.
- **Graph-first, not platform-specific.** The model optimizes for expressing the catalog as a graph that can be joined with existing STIX content — threats, vulnerabilities, identities, assets. It assumes nothing about storage engines, query languages, or UI conventions beyond what STIX-aware platforms already provide.
- **Forward compatibility.** When future STIX versions add SDOs or SCOs, catalog objects relate to them through the same standard `relationship` SRO with no catalog schema changes. The extension layer is forward-compatible by design.
- **Compatibility with SecID, as co-evolving peers.** [SecID](https://secid.cloudsecurityalliance.org/) and this catalog work the same problem space — controls, regulations, mappings, and the identifiers that make them referenceable — and neither is subordinate to the other. The catalog shares SecID's type vocabulary and provenance structure, and uses its dataset metadata for source licensing, because answering the same questions twice in incompatible ways helps nobody. Compatibility is the goal rather than conformance: each project covers ground the other does not, and alignment may move in either direction. SecID's registry is the current source for its own vocabulary.
- **Version coverage follows adoption, not recency.** Where the catalog depends on or references something versioned — a specification, a control framework, a questionnaire — the test is whether a version is actually in use, not whether it is the newest. That cuts both ways.

  *Too new:* a version nobody has implemented is not yet interoperable, and interoperability is the point. STIX 2.1 is the present example; a later STIX version gets adopted when tooling follows it, not on the day it publishes.

  *Still in use:* superseded framework versions are **carried, not deprecated**. Organizations remain certified against earlier editions for years, much existing mapping work targets them, and a catalog that only covered current versions would be unable to describe the compliance landscape people actually occupy. The catalog holds multiple versions of a framework side by side through source-provenance properties, related to each other by `maps-to`, so "the CCM 4.0 view" and "the CCM 4.1 view" are both filters over one graph.

  New content and examples use the current version where nothing argues otherwise. That is a default for authoring, not a statement about what the catalog covers.
- **Exploratory / research status.** The object types and fields are provisional and expected to change as implementation experience accumulates. The goal is to learn which patterns work in practice, not to publish a normative control-modeling standard. Implementers who can meet their needs with standard STIX constructs alone are encouraged to do so and to treat the custom types as optional research-grade extensions.

The *modeling rules* that follow from these principles — how relationships are expressed, how new types are declared, how identifiers work — are conventions rather than principles, and live in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md).

## 2. The format choice: STIX 2.1 with custom SDOs

The proposed back-end representation for catalog content is **STIX 2.1**, with five custom STIX Domain Object types, named to mirror the SecID type vocabulary:

- **`x-control`** — control definitions from any publisher (domain, identifier, specification, ownership, lifecycle relevance, implementation and audit guidance), including CSA's own catalog and the frameworks it harmonizes with.
- **`x-regulation`** — clauses of legally binding law (GDPR, the EU AI Act, NIS2, HIPAA). Standards and control frameworks are `x-control`, not regulations.
- **`x-control-implementation`** — technology-agnostic approaches to fulfilling a control, independent of any product or vendor.
- **`x-capability`** — specific product or service security features, with their configuration, audit, and remediation detail.
- **`x-control-assessment`** — outcomes of self-assessments, audits, or STAR/CAIQ-style evaluations of a specific control.

Field-level definitions are in [`SCHEMA-STIX-OBJECT-EXTENSIONS.md`](SCHEMA-STIX-OBJECT-EXTENSIONS.md); the modeling rules that bind all of them are in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md).

**Why share SecID's type vocabulary.** [SecID](https://secid.cloudsecurityalliance.org/) is CSA's identifier layer for security knowledge. It and this catalog are co-evolving efforts working the same problem space — controls, regulations, mappings, and the identifiers that make them referenceable — and neither is subordinate to the other. Answering the same taxonomy question twice, in incompatible ways, would help nobody, so the catalog adopts SecID's distinctions: it classifies by what an artifact *is* rather than who published it, which is why another framework's controls are controls and only legally binding requirements are regulations.

Three practical benefits follow. Identity is resolvable — a catalog object cites `secid:control/iso.org/27001@2022#A.8.24` and any SecID-aware consumer can dereference it. Provenance is queryable, because a SecID's components decompose into properties that answer questions like "show me every CCM 4.1 control". And source licensing becomes a lookup rather than a per-contribution judgment, since the SecID datasets record redistribution and derivative permissions per source.

Compatibility is the goal rather than conformance. Each project covers ground the other does not — the catalog models implementations and assessments that SecID has no type for — and the expectation is that the two stay legible to each other and learn from each other as both evolve, not that either follows the other.

These objects connect to each other and to the broader STIX object graph through standard STIX `relationship` SROs. They use standard STIX properties (`id`, `created`, `modified`, `created_by_ref`, `labels`, `external_references`, and others) and require no changes to the STIX wire format, versioning model, or transport.

The reasons STIX 2.1 fits the catalog's needs:

**Standards-body grounding.** STIX 2.1 has been an approved OASIS Standard since June 2021. The grammar, type system, and relationship model have years of deployment and refinement behind them. Replicating this from scratch is a multi-year cost for no net benefit.

**First-class extension mechanism.** STIX 2.1 provides an explicit, supported way to declare new object types: an `extension-definition` object declares the extension, and each instance references it through its `extensions` property with `extension_type: "new-sdo"`. This is not a workaround but a designed extension point — the core schema delivers interoperability while extension definitions deliver expressiveness without altering the contract.

The catalog uses that mechanism rather than the STIX 2.0-era practice of inventing an `x-`-prefixed `type` and relying on naming convention, which 2.1 discourages. The difference is practical: because `extension-definition` requires a `schema` property, a consumer encountering an unfamiliar type can retrieve its definition instead of inferring meaning from the name, and two producers that happen to choose the same type name remain distinguishable by the definition identifier their instances reference.

**Native graph model via SROs.** The catalog is fundamentally a graph: controls connect to regulations, to implementations, to assessments, to attack patterns, to vulnerabilities, to threat actors. STIX `relationship` and `sighting` SROs already typed-link any SDO to any other SDO. Expressing "this control mitigates this attack pattern" requires zero new schema work.

**Deployed tooling ecosystem.** STIX and TAXII servers, the OpenCTI platform, MISP, several commercial CTI platforms, and graph databases that already understand STIX all consume the format natively. Catalog content flows into existing infrastructure on day one without translation.

**Direct interoperability with existing CSA STIX content.** CSA's CTI repository at `github.com/CloudSecurityAlliance/cti` is already STIX-formatted. Other CSA threat-intelligence work uses STIX. Choosing STIX for the catalog means it joins a directed graph that already exists across CSA artifacts rather than standing apart from it.

**Direct interoperability with MITRE ATT&CK.** ATT&CK is published as STIX bundles. Linking an `x-control` to an `attack-pattern` is a single SRO away, with no format translation. The same is true for ATLAS, MITRE's adversarial-AI taxonomy.

**Forward compatibility.** When future versions of STIX add new SDOs or SCOs, catalog objects can relate to them via the same `relationship` SRO with no catalog schema changes. The extension layer is forward-compatible by design.

**AI-consumable.** STIX is JSON-native, schema-published, and every object is identifiable by a globally unique ID. AI agents and graph stores can parse and reason about STIX content without bespoke adapters.

## 3. Why not OSCAL as the back-end format?

**OSCAL is a first-class publication format for the catalog.** Section 5 includes OSCAL output as one of the recommended publication formats. OSCAL is excellent at what it was designed for: machine-readable system security plans, component definitions, assessment results, and profile tailoring. Compliance and audit consumers should receive OSCAL.

OSCAL is not, however, the right choice as the catalog's back-end representation. Three reasons:

**Domain fit.** OSCAL is purpose-built for compliance and audit semantics. It is excellent at "here is a system, here are its controls, here are the assessment results." It is less well suited to "this control mitigates this attack pattern, exploited by this threat actor, using this tool." The catalog's intended use spans both domains, and OSCAL covers only one of them.

**Relationship model.** OSCAL has structured links between components and controls, and between assessments and controls, but no general-purpose typed-relationship primitive equivalent to a STIX SRO. Adding new kinds of relationships in OSCAL requires extending the profile or component-definition schema; in STIX, a new relationship type is a string value on a relationship object. The looser, more general STIX model is a better fit for the catalog's graph use case.

**Ecosystem composition.** ATT&CK, threat-intelligence platforms, CSA's own CTI repository — none speak OSCAL. Choosing OSCAL as the back-end format would isolate the catalog from the cyber-threat-intelligence ecosystem it needs to connect to. STIX as the back-end and OSCAL as a publication format gives consumers access to both ecosystems simultaneously.

This is the application of *Alignment over replacement*: the catalog's data model does not replace OSCAL. It serves as an interoperability layer that can produce OSCAL output for compliance audiences while remaining queryable by CTI tools, threat-intelligence platforms, and AI agents.

## 4. Why not a purpose-built custom format?

A custom format would offer total flexibility — and discard every advantage that comes with using a standard:

- No standards-body governance, raising long-term durability and stability questions.
- No existing tooling, requiring custom adapters at every consumer.
- No existing community, training material, or LLM training data, making both human and AI-agent consumption harder.
- No interoperability with adjacent ecosystems (CTI, GRC, ATT&CK, ATLAS, OSCAL).

The *Minimal invention* principle (§1) rules this out: where standard STIX SDOs, SROs, vocabularies, or extension mechanisms suffice, they are preferred.

Other formats that have been considered and not adopted as the back-end representation:

- **CSAF** — purpose-built for vulnerability advisories, not control catalogs. Its deployed publisher base is also far narrower than STIX's, which matters for content that needs to flow unchanged through existing infrastructure.
- **OSV** — optimized for open-source-package vulnerability metadata. Wrong domain.
- **CVE JSON** — the canonical CVE record format. Universal, but a vulnerability-record format, not a control-catalog format.
- **CVRF** — largely supplanted by CSAF; same domain mismatch.
- **RDF, JSON-LD, OWL, and related semantic-web formats** — powerful but heavy. The SecID identifier system already provides graph identity; STIX SROs handle relationships. RDF would be duplicate-purpose for the catalog's needs without commensurate benefit.

## 5. Recommended publication formats and channels

### Formats

The catalog should be published in the following formats, listed by audience:

- **STIX 2.1** — the back-end representation and primary distribution format. Serves cyber-threat-intelligence tools, ATT&CK consumers, and AI agents in graph-aware platforms.
- **OSCAL** — first-class publication format for compliance and audit consumers. Serves NIST-aligned organizations, GRC tooling, and audit workflows.
- **JSON** (plain, schema-published) — universal baseline. Serves developers and generic tooling that need a structured format without STIX or OSCAL dependencies.
- **YAML** — a human-editable, version-control-friendly equivalent of the JSON. Useful for review in pull requests.
- **Excel** — practical format for compliance teams running gap analyses and the existing CCM customer base, which has used Excel exports for over a decade. Pretending spreadsheets are not real publication is fighting reality.
- **CSV** — programmatic spreadsheet consumers and data-pipeline interoperability. Falls out of the Excel work.

Additional formats worth consideration in subsequent releases include CAIQ output for STAR-aligned consumers, HTML and Markdown rendering for web publication, a REST API with OpenAPI specification for live consumers that prefer not to use TAXII, and formal PDF publications for citation and regulatory submission.

### Distribution channels

**GitHub repository** at `https://github.com/CloudSecurityAlliance/SecurityControlsCatalog` is the primary distribution channel. All published formats — STIX bundles, OSCAL component definitions and catalogs, JSON, YAML, Excel workbooks, and CSV exports — are versioned in git, available via clone, GitHub raw URL, or GitHub Releases for tagged cuts. The repository is the distribution channel; no additional infrastructure is required to consume the catalog. **Use of the published catalog in any of these formats is governed by the repository's [`LICENSE.txt`](LICENSE.txt).**

**SecID MCP server** at `https://secid.cloudsecurityalliance.org/mcp` is the live AI-agent channel. Catalog objects registered as SecIDs (for example, `secid:control/cloudsecurityalliance.org/ccm@4.1#CEK-03`) resolve through SecID's existing MCP infrastructure. Any AI session connected to the SecID MCP server can resolve, look up, and describe catalog content directly without bespoke integration.

**CSA MCP server** at `https://cloudsecurityalliance.org/mcp` is planned as a complementary AI-agent channel for direct catalog queries. Until it ships, the SecID MCP server is the AI-agent path.

## 6. Status, scope, and what this document is not

The catalog's data model is **exploratory and research-grade**. The five custom SDOs and the recommendations in this document are provisional. Implementation experience may inform revisions. Implementers who can satisfy their needs with standard STIX constructs alone are encouraged to do so and to treat the `x-*` SDOs as optional, research-grade extensions to be adopted selectively.

This document does not:

- Specify deliverables, sequencing, or timelines.
- Address governance, contribution policy, or feedback channels.
- Replace the catalog's primary data-model design documentation.
- Claim that the catalog's STIX representation is appropriate for the compliance and audit semantics where OSCAL is canonical.
- Define a universal GRC schema or a successor to existing CSA artifacts.

The catalog is intended to complement — not replace — adjacent ecosystems: STIX threat-intelligence data, OSCAL compliance data, MITRE ATT&CK and ATLAS, the CSA Cloud Controls Matrix (CCM), the AI Controls Matrix (AICM), CSA's IoT security work, and the SecID identifier infrastructure. Format and distribution choices should support that complementary role rather than work against it.
