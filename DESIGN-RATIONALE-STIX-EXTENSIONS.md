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

This document outlines the technical rationale behind the format and distribution choices proposed for the CSA Security Controls Catalog ([CloudSecurityAlliance/SecurityControlsCatalog](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog)). It addresses these questions, in the order they depend on each other:

1. Why the catalog has a **back-end representation** at all, distinct from the formats it publishes.
2. Why STIX 2.1 with custom STIX Domain Object (SDO) extensions fills that role.
3. Why not OSCAL — or plain JSON/YAML, CSAF, OSV, RDF, or a purpose-built custom format?
4. What formats and channels should the catalog be published through?
5. Why the committed form is JSON rather than YAML, and how a person reads and corrects it.

**Question 1 is the one that matters most and was previously assumed rather than
argued.** Every other answer here is downstream of it, and a reader who takes STIX to
be *one of* the catalog's output formats — rather than the source the outputs are
generated from — will find the rest of this document arbitrary. Section 2 states the
case.

The arguments here are technical. Specific deliverables, sequencing, and governance are out of scope.

The catalog's data model is exploratory and research-grade. Schemas described in this document are provisional and may evolve as implementation experience accumulates.

### Design principles

These are the principles the catalog's design answers to, and that contributions must respect — violating one is a category error rather than a style nit. **This section is the single home for them**; the other design documents and the repository's context files point here rather than restating them.

- **One canonical representation; every published format is a projection of it.** The catalog holds its content once, in a form chosen to be a **superset of what any output needs**, and each published format is generated from that one source. This is the principle the rest of the design hangs on, and the one most easily lost: a format that *carries* the catalog is not the same kind of thing as a format the catalog is *published in*. Adding an output must be a projection — cheap, mechanical, and lossless in the direction it flows — never a second place where content is authored or semantics are decided. A design in which two formats are both authoritative has no canonical layer at all, and every pair of formats then needs its own conversion and its own answer to what a control or a mapping *means*.
- **Minimal invention.** Introduce new object types or properties only where CSA-CC concepts cannot reasonably be expressed with existing STIX 2.1 objects, vocabularies, or relationships. Standard STIX is preferred over bespoke structures, even at the cost of some CSA-specific convenience.
- **Alignment over replacement.** This work does not replace existing control-modeling efforts — OSCAL in particular — and is not a universal GRC schema. It is an interoperability layer. Do not propose designs that compete with OSCAL; propose ones that interoperate with it.
- **Maximum compatibility with existing tools.** Catalog objects are valid STIX 2.1 and are intended to flow unchanged through existing STIX/TAXII servers, CTI platforms, graph databases, and analysis pipelines. Nothing changes the STIX wire format, versioning model, or transport. If a design would require a consumer to special-case the catalog before it can parse or route the data, the design is wrong.
- **Graph-first, not platform-specific.** The model optimizes for expressing the catalog as a graph that can be joined with existing STIX content — threats, vulnerabilities, identities, assets. It assumes nothing about storage engines, query languages, or UI conventions beyond what STIX-aware platforms already provide.
- **Forward compatibility.** When future STIX versions add SDOs or SCOs, catalog objects relate to them through the same standard `relationship` SRO with no catalog schema changes. The extension layer is forward-compatible by design.
- **Compatibility with SecID, as co-evolving peers.** [SecID](https://secid.cloudsecurityalliance.org/) and this catalog work the same problem space — controls, regulations, mappings, and the identifiers that make them referenceable — and neither is subordinate to the other. The catalog shares SecID's type vocabulary and provenance structure, and uses its dataset metadata for source licensing, because answering the same questions twice in incompatible ways helps nobody. Compatibility is the goal rather than conformance: each project covers ground the other does not, and alignment may move in either direction. SecID's registry is the current source for its own vocabulary.
- **Version coverage follows adoption, not recency.** Where the catalog depends on or references something versioned — a specification, a control framework, a questionnaire — the test is whether a version is actually in use, not whether it is the newest. That cuts both ways.

  *Too new:* a version nobody has implemented is not yet interoperable, and interoperability is the point. STIX 2.1 is the present example; a later STIX version gets adopted when tooling follows it, not on the day it publishes.

  *Still in use:* superseded framework versions are **carried, not deprecated**. Organizations remain certified against earlier editions for years, much existing mapping work targets them, and a catalog that only covered current versions would be unable to describe the compliance landscape people actually occupy. The catalog holds multiple versions of a framework side by side through source-provenance properties, related to each other by `x-gap-mapping` and `superseded-by`, so "the CCM 4.0 view" and "the CCM 4.1 view" are both filters over one graph. The mechanics — new objects per version, what is shared between them, and why the growth is acceptable — are in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md).

  New content and examples use the current version where nothing argues otherwise. That is a default for authoring, not a statement about what the catalog covers.
- **Exploratory / research status.** The object types and fields are provisional and expected to change as implementation experience accumulates. The goal is to learn which patterns work in practice, not to publish a normative control-modeling standard. Implementers who can meet their needs with standard STIX constructs alone are encouraged to do so and to treat the custom types as optional research-grade extensions.

The *modeling rules* that follow from these principles — how relationships are expressed, how new types are declared, how identifiers work — are conventions rather than principles, and live in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md).

## 2. Why a back-end representation at all

Before *which* format, the prior question: why does the catalog have a representation
that is not one of the formats it ships?

Because the catalog's job is to serve audiences that want incompatible things. A GRC
team wants a spreadsheet. An auditor wants OSCAL. A CTI platform wants a STIX graph it
can join to ATT&CK. A developer wants plain JSON with a schema. A reviewer wants
something readable in a pull request. A STAR submission wants a CAIQ workbook. Those
are not variations of one file; they are genuinely different shapes.

There are two ways to serve them.

**Without a canonical layer**, each output is produced from whatever source is nearest
— usually the authoring artifact, sometimes another output. Every output path then has
to answer the modelling questions independently: what identifies a control, what a
mapping asserts, how a framework version relates to its predecessor. Consistency
between outputs becomes a matter of care rather than construction, and the number of
conversions to maintain grows with the number of *pairs* of formats rather than with
the number of formats.

**With a canonical layer**, content is held once in a representation chosen to be a
superset of what every output needs, and each output is a projection of it. The
modelling questions are answered once, in one place, and every format inherits the
answers. Adding a format costs one projection. Correcting a control corrects it
everywhere at once, because there is only one place it exists.

The observable symptom of the first arrangement is that **some outputs carry less than
others, and the gaps are not deliberate**. When a body of control content is published
in several machine-readable formats and one of them is missing the mappings while the
others have them, that is not a decision about audiences — it is one output path having
hit a modelling question the others did not have to answer, with no shared layer in
which to answer it once.

This is also why the back end has to be a **superset**, not a compromise. If the
canonical form can express less than an output needs, that output either loses
information or acquires its own extensions — and it becomes a second authoring surface,
which is the thing being avoided. A back-end format is therefore chosen for expressive
headroom and for whether its semantics can carry the *union* of what the outputs
require, not for whether it is the most convenient format to read.

**The practical consequence, and the one most often mistaken:** the back-end format
being *also* published is incidental. Publishing STIX is useful, because a real
ecosystem consumes STIX directly and it costs nothing to offer the source form. But
STIX's role here is not "one of the output formats, which happens to be first." Treating
it as one candidate output among peers — an alternative to OSCAL or to YAML — is a
different design: it removes the canonical layer and puts every format back to solving
the modelling questions on its own.

## 3. The format choice: STIX 2.1 with custom SDOs

The proposed back-end representation for catalog content is **STIX 2.1**, with a small set of custom STIX Domain Object types, named to mirror the SecID type vocabulary:

- **`x-control`** — control definitions from any publisher (domain, identifier, specification, ownership, lifecycle relevance, implementation and audit guidance), including CSA's own catalog and the frameworks it harmonizes with.
- **`x-regulation`** — clauses of legally binding law (GDPR, the EU AI Act, NIS2, HIPAA). Standards and control frameworks are `x-control`, not regulations.
- **`x-gap-mapping`** — a CSA gap mapping: one control or regulation assessed against a set of targets elsewhere, carrying the `No Gap` / `Partial Gap` / `Full Gap` verdict.
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

**Native graph model via SROs.** The catalog is fundamentally a graph: controls connect to regulations, to implementations, to assessments, to attack patterns, to vulnerabilities, to threat actors. STIX's generic `relationship` SRO already typed-links any pair of objects, SDO or SCO, so expressing "this control mitigates this attack pattern" requires zero new schema work. The other SRO, `sighting`, is narrower and not a general edge: it records that a particular SDO was seen, optionally backed by `observed-data` objects carrying the raw evidence.

**Deployed tooling ecosystem.** STIX and TAXII servers, the OpenCTI platform, MISP, several commercial CTI platforms, and graph databases that already understand STIX all consume the format natively. Catalog content flows into existing infrastructure on day one without translation.

**Direct interoperability with existing CSA STIX content.** CSA's CTI repository at `github.com/CloudSecurityAlliance/cti` is already STIX-formatted. Other CSA threat-intelligence work uses STIX. Choosing STIX for the catalog means it joins a directed graph that already exists across CSA artifacts rather than standing apart from it.

**Direct interoperability with MITRE ATT&CK.** ATT&CK is published as STIX bundles. Linking an `x-control` to an `attack-pattern` is a single SRO away, with no format translation. The same is true for ATLAS, MITRE's adversarial-AI taxonomy.

**Forward compatibility.** When future versions of STIX add new SDOs or SCOs, catalog objects can relate to them via the same `relationship` SRO with no catalog schema changes. The extension layer is forward-compatible by design.

**AI-consumable.** STIX is JSON-native, schema-published, and every object is identifiable by a globally unique ID. AI agents and graph stores can parse and reason about STIX content without bespoke adapters.

## 4. Why not OSCAL as the back-end format?

**OSCAL is a first-class publication format for the catalog.** Section 6 includes OSCAL output as one of the recommended publication formats. OSCAL is excellent at what it was designed for: machine-readable system security plans, component definitions, assessment results, and profile tailoring. Compliance and audit consumers should receive OSCAL.

OSCAL is not, however, the right choice as the catalog's back-end representation. Three reasons:

**Domain fit.** OSCAL is purpose-built for compliance and audit semantics. It is excellent at "here is a system, here are its controls, here are the assessment results." It is less well suited to "this control mitigates this attack pattern, exploited by this threat actor, using this tool." The catalog's intended use spans both domains, and OSCAL covers only one of them.

**Relationship model.** OSCAL has structured links between components and controls, and between assessments and controls, but no general-purpose typed-relationship primitive equivalent to a STIX SRO. Adding new kinds of relationships in OSCAL requires extending the profile or component-definition schema; in STIX, a new relationship type is a string value on a relationship object. The looser, more general STIX model is a better fit for the catalog's graph use case.

**Ecosystem composition.** ATT&CK, threat-intelligence platforms, CSA's own CTI repository — none speak OSCAL. Choosing OSCAL as the back-end format would isolate the catalog from the cyber-threat-intelligence ecosystem it needs to connect to. STIX as the back-end and OSCAL as a publication format gives consumers access to both ecosystems simultaneously.

This is the application of *Alignment over replacement*: the catalog's data model does not replace OSCAL. It serves as an interoperability layer that can produce OSCAL output for compliance audiences while remaining queryable by CTI tools, threat-intelligence platforms, and AI agents.

## 5. Why not a purpose-built custom format?

A custom format would offer total flexibility — and discard every advantage that comes with using a standard:

- No standards-body governance, raising long-term durability and stability questions.
- No existing tooling, requiring custom adapters at every consumer.
- No existing community, training material, or LLM training data, making both human and AI-agent consumption harder.
- No interoperability with adjacent ecosystems (CTI, GRC, ATT&CK, ATLAS, OSCAL).

The *Minimal invention* principle (§1) rules this out: where standard STIX SDOs, SROs, vocabularies, or extension mechanisms suffice, they are preferred.

Other formats that have been considered and not adopted as the back-end representation:

- **Plain JSON or YAML with a published schema** — the most frequently proposed
  alternative, and the one this section previously failed to address. It is entirely
  adequate as a *publication* format, and is listed as one in section 6. It is not a
  candidate for the canonical layer, because **a serialization is not a model.** JSON
  and YAML supply syntax and, with a schema, field validation; they supply no
  relationship primitive, no identity scheme, no mechanism for declaring a new object
  type so a consumer can discover what it means, and no versioning model. Each of those
  would have to be invented — at which point the result is a purpose-built custom
  format wearing a familiar syntax, and every cost listed above applies. The distinction
  is not JSON-versus-STIX: STIX 2.1 *is* JSON. It is whether the catalog also inherits a
  standards-body model, or re-derives one.

  Two consequences are worth stating plainly, because they are the ones a schema does
  not fix. Relationships in a bare-schema design end up as identifier strings inside
  objects, which cannot carry the rationale, confidence, or authorship a contestable
  mapping claim needs, and which no generic tool recognises as edges — see
  [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md) section 1. And a new
  object type is announced only by prose, so two producers emitting the same type name
  are indistinguishable to a consumer, where an `extension-definition` keeps them apart
  by identifier.
- **CSAF** — purpose-built for vulnerability advisories, not control catalogs. Its deployed publisher base is also far narrower than STIX's, which matters for content that needs to flow unchanged through existing infrastructure.
- **OSV** — optimized for open-source-package vulnerability metadata. Wrong domain.
- **CVE JSON** — the canonical CVE record format. Universal, but a vulnerability-record format, not a control-catalog format.
- **CVRF** — largely supplanted by CSAF; same domain mismatch.
- **RDF, JSON-LD, OWL, and related semantic-web formats** — powerful but heavy. The SecID identifier system already provides graph identity; STIX SROs handle relationships. RDF would be duplicate-purpose for the catalog's needs without commensurate benefit.

## 6. Recommended publication formats and channels

### Formats

**The source form, which is also published.** STIX 2.1 is the canonical representation
every other format below is generated from (section 2). It is offered for download as
well, because a deployed ecosystem consumes STIX directly and publishing the source form
costs nothing — but it is listed apart from the others deliberately. It is not a peer of
the formats beneath it; it is what they are projections of. Serves cyber-threat-intelligence
tools, ATT&CK consumers, graph stores, and AI agents in graph-aware platforms.

**Projections of it**, listed by audience. None of these is authoritative, and a
correction belongs in the source rather than in any of them:

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

## 7. Why the committed form is JSON, and how a person reads and corrects it

The catalog's committed form is STIX 2.1 JSON. YAML was proposed for that role and
not adopted. Both halves of that decision need stating, because "JSON is canonical"
answers only half of the question anyone actually has, which is *how do I review
this?*

### Why YAML is not the canonical form

Four reasons, in order of weight:

**It is not what the format is.** STIX 2.1 is defined as JSON. A YAML canon would
mean the catalog's authoritative artifact is not STIX, and every consumer — TAXII
server, CTI platform, graph store, the OASIS validator — would need a conversion step
before it could read anything. That is precisely the *Maximum compatibility* principle
(§1) failing: a design that requires a consumer to special-case the catalog before it
can parse the data is the wrong design.

**Representation ambiguity.** YAML 1.1 and 1.2 disagree about how scalars resolve, and
implementations differ within each. `status: live` is unambiguous; an unquoted `no`,
`yes`, `on`, `off`, `null`, `~`, a leading zero, a bare version number, or a
colon-containing string are not, and different loaders will hand you different values
for identical bytes. A control catalog carries clause identifiers, version strings, and
free prose — exactly the value shapes where this bites. JSON has one reading.

**Weak schema support.** The catalog's contract is JSON Schema, enforced in CI against
every object, and the OASIS STIX validator layers on top. Both take JSON. Validating
YAML means converting to JSON first, which makes JSON the real contract and the YAML a
lossy front end to it.

**Fragility under hand-editing** — and this is the reason worth being careful about,
because it cuts against the usual argument for YAML. YAML's significant indentation
means a whitespace error is a *semantic* error, and the failure is often silent: a
mis-indented key attaches to the wrong parent and still parses. The catalog carries
published control text with carriage returns, tabs, trailing spaces, and typographic
punctuation, which [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md)
section 10 forbids tidying in transit — and YAML block scalars cannot represent several
of those at all. A format chosen *for* hand-editing turns out to be the one that
quietly loses the bytes a human was trying to protect.

### The question that actually matters

None of the above says a person should have to read UUIDs and escaped prose to check
whether a control's audit guidance is right. That is a real objection and it deserved
a real answer rather than a restatement of the format decision. The answer is that
**the form data is stored in and the form a person works in are separate concerns**,
and the second one has to be built rather than asserted.

So it is built. [`tools/yaml_view.py`](tools/) renders any committed object as YAML
with the machinery removed, and takes an edited rendering back to the exact JSON:

```sh
python3 tools/yaml_view.py objects/x-control/cloudsecurityalliance.org/aicm/1.1.0/MDS-01.json
python3 tools/yaml_view.py --write edited.yaml
python3 tools/yaml_view.py --check     # every committed object, round-tripped
```

Three properties of that tool are what make it an answer rather than a gesture:

**The view drops only what was never authored.** The properties it withholds —
`spec_version`, `id`, `created`, `modified`, `object_marking_refs`, `extensions`,
`created_by_ref` — are each either constant across the whole catalog or minted once and
permanent. `catalog.reconcile` exists so that regenerating an object does not disturb
them. The UUIDs and timestamps that make the JSON unpleasant to read are bookkeeping,
not content a reviewer has an opinion about, and they are restored mechanically from
the type and the committed object.

**Write-back produces a minimal diff.** Correcting a domain name in the view and
writing it back changes that property and `modified`, and nothing else. The identifier
is preserved, so no consumer's reference breaks.

**Losslessness is enforced, not claimed.** `--check` renders every committed object,
reads it back, and requires byte equality with the file on disk; it runs in CI. The
writer uses a readable block scalar only where that is provably lossless and falls back
to a quoted scalar otherwise — which is the YAML fragility above, handled by a tool
instead of by a contributor's care.

What the view deliberately does *not* do is author new objects. An object's identifier
is minted once (conventions section 3), and catalog content comes from published source
releases through the generators in `tools/`. The view is for reviewing and correcting
what is already committed — which is what a contributor actually does — not for adding
a control by hand.

**And a correction made here is not durable, which the tool states on every write.**
Nothing under `objects/` is hand-authored: every object is generated, and
`catalog.reconcile` preserves only `id` and `created` while taking all content from the
generator. A view that can write is therefore a **second writer with no precedence over
the first** — a genuine single-source-of-truth problem, and one introduced by the view
itself rather than by the model it renders. The authoritative source for catalog content
is the published release the generator reads; the view is a rendering of the derived
copy.

Leaving that implicit would be the worse failure: a contributor who fixes a typo and
watches it disappear a release later has been misled by the tool. So a write names the
generator that will overwrite it and both remedies — **upstream** if the publisher's data
is wrong (section 10 forbids tidying it in transit, so the fix belongs there and the
conversion follows), or **the generator** if the conversion is wrong. Whether the catalog
should instead be able to *hold* a correction across regeneration — an overlay carried
separately from the derived objects — is a real design question and is tracked as one.

**The consequence for contribution.** A contributor does not need to read or write STIX
to correct catalog content: they read a YAML rendering, edit it, and write it back, and
CI checks the result against the schemas. The tooling is a convenience for contributors,
not a dependency for consumers — the published catalog stays plain JSON, and nothing is
required to consume it.

## 8. Status, scope, and what this document is not

The catalog's data model is **exploratory and research-grade**. The custom SDOs and the recommendations in this document are provisional. Implementation experience may inform revisions. Implementers who can satisfy their needs with standard STIX constructs alone are encouraged to do so and to treat the `x-*` SDOs as optional, research-grade extensions to be adopted selectively.

This document does not:

- Specify deliverables, sequencing, or timelines.
- Address governance, contribution policy, or feedback channels.
- Replace the catalog's primary data-model design documentation.
- Claim that the catalog's STIX representation is appropriate for the compliance and audit semantics where OSCAL is canonical.
- Define a universal GRC schema or a successor to existing CSA artifacts.

The catalog is intended to complement — not replace — adjacent ecosystems: STIX threat-intelligence data, OSCAL compliance data, MITRE ATT&CK and ATLAS, the CSA Cloud Controls Matrix (CCM), the AI Controls Matrix (AICM), CSA's IoT security work, and the SecID identifier infrastructure. Format and distribution choices should support that complementary role rather than work against it.
