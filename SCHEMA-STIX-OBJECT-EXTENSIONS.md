---
title: "STIX Object Extensions for the CSA Security Controls Catalog (CSA-CC)"
document-status: DRAFT
created: 2025-07-22
date: 2026-07-29
author: "CSA Security Controls Catalog working group"
status: "Provisional — exploratory / research status"
type: "Schema definition"
tags: [security-controls-catalog, stix, schema, oscal, secid, sdo]
---

# STIX Object Extensions for the CSA Security Controls Catalog (CSA-CC)

This document defines five custom STIX 2.1 object types — `x-control`,
`x-regulation`, `x-control-implementation`, `x-capability`, and
`x-control-assessment` — designed to represent and operate the CSA Security
Controls Catalog (CSA-CC) in a machine-readable, graph-relational format. It also
maps each object type to the relevant portions of the CSA-CC architecture and
rationale.

The types are declared using STIX 2.1's **extension-definition** mechanism rather
than as bare custom objects — see
[How these objects extend STIX 2.1](#how-these-objects-extend-stix-21). The `x-`
prefix is retained for readability, though the mechanism no longer requires it.

> **Scope and precedence.** Three documents divide the design, by the question
> they answer:
>
> | Question | Document |
> |---|---|
> | **Why** STIX 2.1 | [`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) |
> | **How** we use STIX | [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md) |
> | **What** each object carries | this document |
>
> Each document governs its own column, and where two touch the same subject the
> one whose column it is governs. All three are provisional — see
> [Open questions](#open-questions) here and in the conventions document for what
> is not settled.

## Design principles

The principles this schema answers to are defined once in
[`DESIGN-RATIONALE-STIX-EXTENSIONS.md` § Design principles](DESIGN-RATIONALE-STIX-EXTENSIONS.md#design-principles),
and are neither restated nor listed here.

Two of them bear directly on reading this document: fields and object boundaries
mirror the catalog's own structure and align conceptually with OSCAL rather than
competing with it, and every type and property below is provisional.

## The object model at a glance

The five types form a layered chain from requirement to product feature, plus
assessment:

```
x-regulation                 GDPR Art. 32(1)(a)          what the law requires
     ↑ csa-gap-mapping
x-control                    "sensitive data is encrypted at rest"
     ↑ csa-gap-mapping       ← also to other frameworks' x-control objects
     ↑ (relationship not yet defined)
x-control-implementation     "enforce encryption at rest for object storage"
     ↑ (relationship not yet defined)
x-capability                 Amazon S3 SSE-KMS           what a product provides

x-control-assessment  →  evaluates an x-control, via embedded constitutive refs
```

Only the mapping relationship is defined today. The edges into
`x-control-implementation` and `x-capability` are deliberately left undefined until
instance data needs them — see
[Relationship types deliberately not yet defined](#relationship-types-deliberately-not-yet-defined).

Each layer changes on a different timescale, which is why they are separate
objects: a control is stable for years, an implementation approach changes with
architecture, and a capability changes whenever a vendor ships.

### Type alignment with SecID

The catalog and [SecID](https://secid.cloudsecurityalliance.org/) are co-evolving
projects in the same problem space, so object types share SecID's type vocabulary
and the same conceptual distinctions hold across both:

| STIX type | SecID type | Notes |
|---|---|---|
| `x-control` | `control` | **Any** publisher's controls — CSA CCM and AICM, ISO 27001, NIST 800-53/CSF, CIS, PCI DSS, SOC 2 |
| `x-regulation` | `regulation` | Legally binding requirements only — GDPR, the EU AI Act, NIS2, DORA, HIPAA |
| `x-capability` | `capability` | Product and service security features |
| `x-control-implementation` | — | No SecID counterpart at present |
| `x-control-assessment` | — | No SecID counterpart at present |

The two rows without a counterpart are ground the catalog covers and SecID does
not; SecID likewise covers ground the catalog does not. Neither is a deficit, and
alignment may move in either direction as both projects evolve — see
[conventions § 3](CONVENTIONS-STIX-MODELING.md).

SecID classifies by what an artifact *is*, not by who published it, and the
catalog adopts that distinction. One consequence worth stating plainly: **another
framework's controls are `x-control` objects, not regulations.** ISO 27001 A.8.24
is a control; GDPR Article 32 is a regulation. SecID's registry puts it as
"regulations are what you must comply with, controls are how you comply."

The two SecID types the catalog does **not** model as objects are `reference` and
`methodology`. A reference (ISO 27000's vocabulary, for instance) is a citation,
which is what `external_references` is for; a methodology (ISO 27005, NIST IR
8477) is cited the same way, most usefully on a mapping relationship to record
how the mapping was derived. Creating SDOs for either would fail the
custom-property test in [conventions § 4](CONVENTIONS-STIX-MODELING.md).

### Source provenance

Objects that represent third-party content carry the components of their SecID as
separate queryable properties, rather than only a single SecID string. The
decomposition matters: `"secid:control/iso.org/27001@2022#A.8.24"` as one opaque
string cannot answer "show me every CCM 4.1 control," while separate properties
can. The full SecID also appears in `external_references`.

For `x-control` the properties are `framework_namespace`, `framework`,
`framework_version`, and `control_identifier`, mirroring
`secid:control/<namespace>/<name>@<version>#<subpath>`.

This is what lets CSA's own catalog and the frameworks it harmonizes coexist in
one object type: `cloudsecurityalliance.org/ccm@4.1` and
`cloudsecurityalliance.org/scc` sit side by side, related by `csa-gap-mapping`, and "the
CCM view" is a property filter rather than a separate export.

## How these objects extend STIX 2.1

The five types are declared through STIX 2.1's **extension-definition** mechanism,
not as bare custom objects.

STIX 2.0 introduced new object types by using an `x-`-prefixed `type` value and
relying on naming convention. STIX 2.1 adds an explicit mechanism instead: an
`extension-definition` SDO declares the extension, and each instance of the new
type references it. The specification titles its custom-object section "Custom
Objects (Deprecated)" — producers may still use that approach, but extension
definitions are the preferred standardized path, and the catalog takes the
preferred one.

Three practical gains follow, and the third is the reason this matters most:

- **Consumers can discover what the type means.** `extension-definition` requires a
  `schema` property, so a platform encountering `x-control` can retrieve its
  definition instead of guessing from the name.
- **The catalog uses the current mechanism**, rather than a deprecated one, which is
  hard to reconcile with a stated principle of maximum compatibility.
- **Type names stop being ambiguous.** Two producers may both emit `x-control`, but
  their instances reference different extension-definition identifiers, so a
  consumer can tell them apart. The namespace lives in the identifier, where it
  belongs, rather than in a lengthened type string.

### One extension-definition per type

Each of the five types has its own `extension-definition` object rather than
sharing one. Nothing in STIX requires this — an instance carries its own `type`
property, so a single shared definition would still leave consumers able to tell
the types apart. The reason is **change isolation**.

Definition identifiers are permanent once published, and this model is explicitly
research-grade and expected to change. Suppose implementation experience shows
`x-control-implementation` should be absorbed into `x-capability`:

- With separate definitions, that one definition is retired with a migration note.
  The other four are untouched, and their consumers are unaffected.
- With a shared definition, the choice is to bump `version` on a definition
  covering four types that did not change — misinforming those consumers about what
  moved — or to mint a replacement and invalidate the references on every object of
  all five types.

A shared definition couples the stability of unrelated types together. Per-type
definitions also give targeted discovery, since `name`, `description`, and `schema`
describe one type rather than an omnibus, and let each type carry its own
`version`.

The commonly cited benefit of *partial adoption* is weak here and worth
discounting: the types are interdependent, and `x-capability` is not meaningful
without `x-control-implementation` and `x-control`.

```json
{
  "type": "extension-definition",
  "spec_version": "2.1",
  "id": "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "CSA Security Controls Catalog — x-control",
  "description": "A security control from any publisher, with its specification, guidance, lifecycle state, and source provenance.",
  "schema": "https://raw.githubusercontent.com/CloudSecurityAlliance/SecurityControlsCatalog/refs/heads/main/schemas/x-control.json",
  "version": "1.0",
  "extension_types": ["new-sdo"]
}
```

Every instance of an extended type then carries:

```json
"extensions": {
  "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea": {
    "extension_type": "new-sdo"
  }
}
```

**The five definition identifiers are minted and are now permanent.** They live as
committed objects in [`objects/extension-definition/`](objects/extension-definition/),
and instance data must reference the real values shown in the examples below — a
consumer that has ingested catalog content keys off them, so changing one is a
breaking change rather than an edit.

Remaining `<UUID>` placeholders stand for per-object identifiers, which are minted
when an object is created and then fixed by being committed to a file.

`schema` points at the machine-readable JSON Schema for the type, in
[`schemas/`](schemas/). Those schemas validate what is settled and stay silent about
what is not — see [`schemas/README.md`](schemas/README.md) for what they
deliberately do not check. This document remains the normative definition of what
each property *means*; where the two disagree, this document wins and the schema has
a bug.

The URL currently tracks `main`, which suits a draft but not published content: a
released bundle should reference a tagged, immutable URL so the definition cannot
shift under objects already ingested. See [Open questions](#open-questions).

Standard STIX objects the catalog uses — `relationship`, `identity`,
`marking-definition`, `attack-pattern` — are **not** extended and carry no
`extensions` property. Only the five custom types do.

Because a consumer cannot interpret an instance without its definition, **the
extension-definition objects must travel with the content** in every published
bundle. That constrains bundle composition, which is tracked as an open question in
the conventions document.

## Maximum compatibility with existing and future data

By modeling CSA-CC as first-class STIX 2.1 objects and relying on the standard
`relationship` SRO, the CSA extensions can attach directly to any existing or
future STIX content without custom wiring.

**Native relationship mapping to all current STIX Domain Objects (SDOs).** Any
catalog object can be related to existing SDOs using the standard `relationship`
object. This enables, for example:

- A control that **mitigates** an `attack-pattern` or malware family.
- A capability that **protects** or **hardens** specific infrastructure
  components.
- A control mapped to `campaign`, `intrusion-set`, or `threat-actor` objects to
  express which adversary behaviors it is designed to counter.
- Controls and capabilities tied into `indicator` and `observed-data` for
  detection and telemetry coverage.
- Assessment results linked to `report`, `grouping`, `note`, or `opinion` objects
  for narrative, analyst commentary, and disagreement.

Under STIX 2.1 these links use the same `relationship` SRO as the rest of the CTI
ecosystem, so existing STIX/TAXII servers, CTI platforms, and graph stores need
no special logic to handle CSA-CC objects.

**Full compatibility with cyber-observable data (SCOs).** Because the
`relationship` SRO can connect SDOs to SCOs, catalog objects can be wired
directly to low-level observables (`file`, `network-traffic`, `ipv4-addr`, `url`,
`process`, `user-account`, `x509-certificate`) that represent the technical
evidence or enforcement points for a control. This supports use-cases like:

- "Which CSA-CC controls are actually enforced on the observables seen in this
  incident?"
- "Which `x-capability` objects correspond to the particular software and
  infrastructure in this environment?"

**No custom wire format, and forward compatibility.** The CSA-CC objects are
ordinary STIX SDOs declared through the standard extension-definition mechanism,
using standard STIX properties (`id`, `spec_version`, `created`, `modified`,
`created_by_ref`, `labels`, `external_references`, `extensions`, and others). They
participate in relationships exactly like any other SDO.

- If a future STIX version adds new SDOs or SCOs, the CSA objects can relate to
  them immediately via the same `relationship` SRO.
- No changes are required to the CSA object schemas to take advantage of new STIX
  object types; the relationship layer already abstracts that away.

**Interoperability with existing CTI and GRC data.** Because we are not defining
a parallel relationship system, CSA-CC can be overlaid on top of:

- Existing STIX CTI graphs (MITRE ATT&CK-mapped `attack-pattern` data, vendor
  threat reports, and similar).
- Internal detection content modeled as `indicator` plus SCOs.
- GRC content already exported as STIX `report`, `grouping`, or `vulnerability`
  information.

The net effect is that a control catalog becomes just another well-typed subgraph
in the broader STIX ecosystem, not a separate data silo.

### Current STIX 2.1 objects we can map to

Using the standard `relationship` SRO, CSA-CC objects can map to **all STIX 2.1
Domain Objects** and **Cyber-observable Objects**, including at least:

**STIX Domain Objects (SDOs):** `attack-pattern`, `campaign`, `course-of-action`,
`grouping`, `identity`, `indicator`, `infrastructure`, `intrusion-set`,
`location`, `malware`, `malware-analysis`, `note`, `observed-data`, `opinion`,
`report`, `threat-actor`, `tool`, `vulnerability`.

**STIX Relationship Objects (SROs):**

- `relationship` — links any pair of objects, SDO or SCO, with a typed semantic
  such as *mitigates*, *uses*, or *indicates*. This is the general edge type and
  the one the catalog uses.
- `sighting` — records that a particular SDO was seen, optionally backed by
  `observed-data` objects carrying the raw evidence. Narrower than `relationship`:
  its required `sighting_of_ref` names the SDO that was sighted, not an arbitrary
  object, so it is not a general-purpose link.

**Representative STIX Cyber-observable Objects (SCOs):** `artifact`,
`autonomous-system`, `directory`, `domain-name`, `email-addr`, `email-message`,
`file`, `ipv4-addr`, `ipv6-addr`, `mac-addr`, `mutex`, `network-traffic`,
`process`, `software`, `url`, `user-account`, `windows-registry-key`,
`x509-certificate`.

If your STIX graph can represent it, these CSA-CC objects can be related to it
without any additional protocol, schema, or transport changes.

Implementers who can satisfy their immediate needs with standard STIX constructs
alone are encouraged to do so, and to treat these `x-*` objects as optional,
research-grade extensions to be adopted selectively.

---

## Relationships use SROs, not embedded references

Relationships between CSA-CC objects are expressed with the standard STIX
`relationship` SRO, **not** as arrays of identifiers inside the objects
themselves.

The reasoning — a mapping is a claim needing its own rationale, confidence, and
authorship; generic STIX tooling traverses SROs and not custom properties; and
controls should version independently of the claims made about them — is in
[`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md) § 1, along with the
test for when an embedded reference is still correct. This section records only
which edges exist.

### Canonical edges

**One relationship type is defined: `csa-gap-mapping`.**

| Assertion | `relationship_type` | Source | Target |
|---|---|---|---|
| How much of the source's requirement the target covers | `csa-gap-mapping` | `x-control` or `x-regulation` | `x-control` or `x-regulation` |

Read left to right, as CIS does: `source_ref` is what is mapped **from**. A→B and
B→A are two separate objects, each with its own verdict, because coverage is not
symmetric — B may fully cover A while A covers only part of B. Where the relation
*is* symmetric, `bidirectional: true` says so explicitly, since STIX relationships
are directional by construction.

The custom properties `gap_level` and `bidirectional` are declared by a
**`toplevel-property-extension`** rather than added bare. `relationship` is a
standard STIX type, so an undeclared custom property on it could collide with
another producer's property of the same name; the extension scopes them. This is the
same mechanism the five SDOs use, with a different `extension_type`.

`relationship_type` carries the methodology, so no separate field does. A future
`nist-ir-8477-mapping` would be a sibling type with its own properties rather than
this one overloaded with a second vocabulary.

### Relationship types deliberately not yet defined

`implements`, `supports`, and `superseded-by` were sketched in earlier revisions and
are **withdrawn until something needs them** — a custom relationship type is a public
commitment, and none of the three has instance data behind it yet. `mitigates` is
standard and available whenever a control is related to an `attack-pattern`; the
catalog simply does not assert it yet, and MITRE's Mappings Explorer already owns
that space.

When replacement does need expressing, the reasoning recorded earlier still applies:
not ATT&CK's `revoked-by`, since supersession is not revocation and historical
assessments against a superseded control remain true, and not the standard
`derived-from`, which says only that one object came from another. Note also that
CCM's own published mappings include a CCM 3.0.1 target, so version succession may
turn out to be expressible as an ordinary mapping.

### A worked mapping

Showing what an embedded identifier array could not express — the verdict, the
rationale, and the authorship of the claim:

```json
{
  "type": "relationship",
  "spec_version": "2.1",
  "id": "relationship--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "relationship_type": "csa-gap-mapping",
  "source_ref": "x-control--<UUID>",
  "target_ref": "x-regulation--<UUID>",
  "extensions": {
    "extension-definition--025268d9-bd6e-44e0-a3d5-b18821232903": {
      "extension_type": "toplevel-property-extension"
    }
  },
  "gap_level": "Partial Gap",
  "bidirectional": false,
  "description": "The control requires encryption of sensitive data at rest and in transit; the target clause requires encryption of personal data. Partial coverage — the control's scope is broader than personal data.",
  "external_references": [
    {
      "source_name": "secid",
      "external_id": "secid:methodology/nist.gov/ir-8477"
    }
  ]
}
```

The `external_references` entry records the methodology the mapping was derived
under — provenance that belongs on the claim, not on either endpoint.

The one exception to the SRO rule in this model is `x-control-assessment`, whose
`assessed_control_ref` and `entity_ref` stay embedded because they are
constitutive of the object — see
[`CONVENTIONS-STIX-MODELING.md` § Constitutive references stay embedded](CONVENTIONS-STIX-MODELING.md#constitutive-references-stay-embedded).

---

## 1. `x-control` — a security control

### Description

Represents a security control: a requirement stating what must be true, together
with guidance on implementing and auditing it. Controls from **any** publisher are
this type — CSA's own catalog, CCM, AICM, ISO 27001, NIST 800-53 and CSF, CIS
Benchmarks, PCI DSS, SOC 2 — distinguished by their source provenance properties
rather than by object type.

Mappings to other frameworks are **not** properties of the control; they are
`csa-gap-mapping` relationship SROs. See
[Relationships use SROs, not embedded references](#relationships-use-sros-not-embedded-references).

### Schema

A CSA control, carrying CSA's own specification text. This example is a real
control — CCM 4.1 CEK-03 — so its identifiers, domain, and applicability can be
checked against the published matrix rather than taken on trust:

```json
{
  "type": "x-control",
  "spec_version": "2.1",
  "id": "x-control--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea": {
      "extension_type": "new-sdo"
    }
  },
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "Data Protection",
  "framework_namespace": "cloudsecurityalliance.org",
  "framework": "ccm",
  "framework_version": "4.1",
  "control_identifier": "CEK-03",
  "domain": "Cryptography, Encryption & Key Management",
  "status": "live",
  "specification": "Data protection at rest, in transit, and where applicable in use is provided using cryptographic libraries certified to approved standards.",
  "ownership": ["CSP", "CSC"],
  "applicability": ["IaaS", "PaaS", "SaaS"],
  "stack_components": ["network", "storage", "data"],
  "lifecycle_relevance": ["deployment", "retirement"],
  "implementation_guidance": "...",
  "audit_guidance": "...",
  "labels": ["cloud", "compliance"],
  "external_references": [
    {
      "source_name": "secid",
      "external_id": "secid:control/cloudsecurityalliance.org/ccm@4.1#CEK-03"
    }
  ]
}
```

A third-party control whose licence does not permit reproducing its text. The
object is a **pure citation**: the standard number and the clause identifier, and no
prose at all — no title, no excerpt, no paraphrase. `name` holds a citation the
catalog constructs from the provenance fields, so the object renders legibly in
generic STIX tools without carrying any of the publisher's text. This is the same
minimum CCM and AICM use when citing these sources:

```json
{
  "type": "x-control",
  "spec_version": "2.1",
  "id": "x-control--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea": {
      "extension_type": "new-sdo"
    }
  },
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "ISO/IEC 27001:2022 A.8.24",
  "framework_namespace": "iso.org",
  "framework": "27001",
  "framework_version": "2022",
  "control_identifier": "A.8.24",
  "status": "live",
  "external_references": [
    {
      "source_name": "secid",
      "external_id": "secid:control/iso.org/27001@2022#A.8.24"
    }
  ]
}
```

> **`specification` holds reproduced text and is therefore licence-constrained.**
> Populate it for CSA's own controls, and for third-party controls only where the
> source permits reproduction. Where it does not, the object carries citation
> metadata only — the schema enforces this for `iso.org` and `iec.ch` by rejecting
> `specification`, `description`, `implementation_guidance`, and `audit_guidance`
> on those objects. See [conventions § 8](CONVENTIONS-STIX-MODELING.md).

### `status`, `revoked`, and supersession

`status` carries the control's lifecycle: `draft`, `live`, or `retired`. The three
are mutually exclusive, which is why this is an enum rather than a set of
booleans — no combination of flags can put a control in two lifecycle states at
once.

The standard STIX `revoked` property is **orthogonal to `status`, not a substitute
for `retired`.** They record different facts:

| | Meaning | Effect on prior assessments |
|---|---|---|
| `status: "retired"` | The control was valid but is no longer current | Prior `x-control-assessment` objects remain true statements about their assessment date |
| `revoked: true` | The control is withdrawn as invalid — published in error | Assessments against it are void; consumers should disregard the object |

This distinction is load-bearing. STIX consumers routinely filter `revoked: true`
objects out entirely, so using `revoked` to mean "retired" would silently
invalidate the catalog's own assessment history: an audit performed in 2024
against a control retired in 2026 is still a true statement about 2024. Retirement
must therefore not be expressed with `revoked`.

Replacement is not a `status` value. A control replaced by a newer one gets
`status: "retired"`, and the replacement is expressed as a relationship rather than a
property, because it is an assertion about two objects carrying its own date,
rationale, and authorship, and because the retired control remains coherent without
it. The relationship type for that is not yet defined — no content has retired
controls — see
[Relationship types deliberately not yet defined](#relationship-types-deliberately-not-yet-defined).

### CSA-CC alignment

- **Control data model** — captures domain, identifier, ownership, lifecycle
  relevance, and architectural relevance.
- **Mapping / gap analysis** — links to other frameworks' controls and to binding
  law via `csa-gap-mapping` SROs, each carrying its own coverage verdict.
- **Specification, implementation, and auditing guidelines** — represented
  directly.
- **Status and governance** — supports control lifecycle via `status`. Replacement
  is a relationship rather than a status value, and the standard
  STIX `revoked` property remains available for the distinct case of a control
  withdrawn as invalid.

---

## 2. `x-regulation` — a clause of binding law

### Description

Represents a legally binding requirement: a clause, article, or section of a law,
regulation, or directive. GDPR, the EU AI Act, NIS2, DORA, HIPAA, and CCPA are
this type.

**Standards and control frameworks are not regulations.** ISO 27001, NIST 800-53,
PCI DSS, and SOC 2 are `x-control` objects, following SecID's distinction between
what you must comply with and how you comply.

Many regulations are unversioned — GDPR is identified as Regulation (EU) 2016/679
rather than by a version number — so `regulation_version` is optional. Where a
regulation is amended, the date an amendment came into effect is the practical
discriminator.

### Schema

```json
{
  "type": "x-regulation",
  "spec_version": "2.1",
  "id": "x-regulation--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--a72496a3-08f8-43fb-88c9-479bb94e5e02": {
      "extension_type": "new-sdo"
    }
  },
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "Security of processing — pseudonymisation and encryption",
  "regulation_namespace": "europa.eu",
  "regulation": "gdpr",
  "clause_identifier": "art-32/1/a",
  "publication_id": "Regulation (EU) 2016/679",
  "text_excerpt": "the pseudonymisation and encryption of personal data",
  "jurisdiction": "EU",
  "labels": ["encryption", "data-protection"],
  "external_references": [
    {
      "source_name": "secid",
      "external_id": "secid:regulation/europa.eu/gdpr#art-32/1/a"
    },
    {
      "source_name": "EUR-Lex",
      "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
    }
  ]
}
```

`text_excerpt` is populated here because the source's record permits reproduction
with attribution — EU legislative text is reusable. Check the source record for the
specific terms rather than relying on a value quoted in this document. Where a
source does not permit reproduction, omit `text_excerpt` and describe the
requirement in original wording. See
[conventions § 8](CONVENTIONS-STIX-MODELING.md).

### CSA-CC alignment

- **Mapping / gap analysis** — enables dynamic, decoupled mapping between controls
  and legal requirements.
- **Interoperability objective** — links CSA controls to the legal and regulatory
  landscape.
- **Mapping guidelines and protocols** — supports traceable mappings and
  compensating control logic.

---

## 3. `x-control-implementation` — a technology-agnostic implementation approach

### Description

Represents *how* a control is fulfilled, stated independently of any product or
vendor: "enforce encryption at rest for object storage", "implement guardrails for
AI output". It is the bridge between a control's requirement and the specific
product features that provide it.

Implementations carry no vendor, product, or configuration detail — those belong to
`x-capability` (section 4 below). An implementation approach outlives the products
that implement it.

### Schema

```json
{
  "type": "x-control-implementation",
  "spec_version": "2.1",
  "id": "x-control-implementation--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--1690104a-d3f2-4716-a334-252356f338dc": {
      "extension_type": "new-sdo"
    }
  },
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "Enforce encryption at rest for object storage",
  "description": "Require that object storage enforces server-side encryption with customer-managed keys, and that unencrypted writes are rejected rather than silently accepted.",
  "implementation_type": ["configuration", "policy-enforcement"],
  "stack_components": ["storage"],
  "labels": ["cloud", "customer-owned"]
}
```

### CSA-CC alignment

- **Implementation guidelines** — reflects how to fulfill a control. The
  relationship linking an implementation to the controls it fulfills is not yet
  defined; see
  [Relationship types deliberately not yet defined](#relationship-types-deliberately-not-yet-defined).
- **Stack component applicability** — for example network, app, storage.
- **Ownership and responsibility** — encoded through labels.

---

## 4. `x-capability` — a product or service security feature

### Description

Represents a specific security feature of a specific product or service, together
with how it is configured, audited, and remediated: Amazon S3 server-side
encryption with KMS keys, AWS CloudTrail, Azure AI Content Safety, Bedrock
Guardrails. A capability **supports** one or more implementation approaches, and
through them the controls those approaches fulfill.

This is the only layer that is vendor-specific, and the only one that changes on a
vendor's release cadence. Capabilities should stay thin: point at
`secid:capability/...` and the vendor's own documentation rather than mirroring
product detail that changes weekly.

### Schema

```json
{
  "type": "x-capability",
  "spec_version": "2.1",
  "id": "x-capability--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--43f8f73f-45e2-4d06-bdc0-46bdd5cb3e81": {
      "extension_type": "new-sdo"
    }
  },
  "created_by_ref": "identity--51f9d480-d80b-4415-93c7-507cde4d1e85",
  "name": "Amazon S3 server-side encryption with AWS KMS keys (SSE-KMS)",
  "description": "S3 encrypts objects at rest using a KMS-managed key; bucket policy can reject requests that do not specify SSE-KMS.",
  "vendor_namespace": "amazon.com",
  "product": "aws/s3",
  "capability_type": ["encryption-at-rest", "key-management"],
  "config_snippet": "resource \"aws_s3_bucket_server_side_encryption_configuration\" { ... }",
  "labels": ["IaaS", "storage", "customer-owned"],
  "external_references": [
    {
      "source_name": "secid",
      "external_id": "secid:capability/amazon.com/aws/s3"
    },
    {
      "source_name": "AWS documentation",
      "url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html"
    }
  ]
}
```

### CSA-CC alignment

- **Controls engineering** — gives control-as-code and architectural-embedding
  guidance somewhere concrete to attach.
- **Automation** — the configuration, audit, and remediation detail a pipeline
  needs in order to check a control mechanically.

---

## 5. `x-control-assessment` — a control assessment result

### Description

Captures the outcome of a self-assessment, audit, or STAR questionnaire evaluating
the implementation status of a specific control for a specific entity. May include
evidence, status, timestamp, and scoring.

`assessed_control_ref` and `entity_ref` are embedded rather than expressed as
SROs: an assessment with no assessed control and no assessed entity is incoherent,
so both are constitutive properties, following the STIX `sighting` pattern. See
[`CONVENTIONS-STIX-MODELING.md` § Constitutive references stay embedded](CONVENTIONS-STIX-MODELING.md#constitutive-references-stay-embedded).

### Schema

```json
{
  "type": "x-control-assessment",
  "spec_version": "2.1",
  "id": "x-control-assessment--<UUID>",
  "created": "2026-01-15T00:00:00.000Z",
  "modified": "2026-01-15T00:00:00.000Z",
  "extensions": {
    "extension-definition--c2b74dc8-5ea7-4d9c-ade0-85474e5f70b4": {
      "extension_type": "new-sdo"
    }
  },
  "assessed_control_ref": "x-control--<UUID>",
  "entity_ref": "identity--<UUID>",
  "assessment_status": "implemented",
  "assessment_type": "self-assessment",
  "assessment_date": "2026-01-14T00:00:00.000Z",
  "evidence_description": "Cloud provider security attestation plus encryption configuration logs",
  "score": 90,
  "labels": ["CAIQ", "STAR"]
}
```

### CSA-CC alignment

- **CAIQ module** — captures structured response per control.
- **Assessment, metrics, and monitoring** — enables tracking of compliance
  posture.
- **Reporting and presentation layer** — feeds dashboards and GRC platforms.

---

## Summary of coverage

| STIX object | Covers CSA-CC section(s) |
|---|---|
| `x-control` | Control data model, specification, lifecycle, ownership, guidelines, threat relevance, cross-framework harmonization |
| `x-regulation` | Regulatory traceability, legal mapping and gap analysis |
| `x-control-implementation` | Implementation guidelines, architectural relevance, ownership |
| `x-capability` | Controls engineering, automation, configuration and audit detail |
| `x-control-assessment` | CAIQ, metrics and monitoring, assessment results, presentation dashboard |

## Open questions

Unsettled as of this revision. Contributions that depend on any of these should
raise an issue rather than assume an answer.

1. **A tagged, immutable schema URL for release.** The schemas exist in
   [`schemas/`](schemas/), but each `schema` property points at `main`, so the
   definition can change under objects already ingested. A released bundle should
   reference a tagged URL. Two further tightenings wait on the model settling:
   `additionalProperties` is unrestricted, so typos pass, and most vocabularies are
   open string arrays.
2. **A set-theory relation alongside `gap_level`, for interoperability.** CSA's gap
   vocabulary is coverage-directional and is what the catalog uses. It is also the
   outlier: NIST OLIR (IR 8278A), NIST IR 8477, the Secure Controls Framework's STRM,
   CIS's mappings, and — since March 2026 — the OSCAL Mapping Model all express
   mappings as set-theory relations (`subset-of`, `superset-of`, `intersects-with`,
   `equal-to`, `no-relationship`). The gap vocabulary does not map onto those
   losslessly: `No Gap` does not distinguish `subset-of` from `equal-to`. Since OSCAL
   is a first-class publication format and alignment with it is a stated principle,
   carrying a set-theory relation as an additional property is probably needed before
   OSCAL output is meaningful. Deferred deliberately — CSA's own vocabulary comes
   first.
3. **How the annual *Top Threats to Cloud Computing* list is referenced.** Whether
   each threat becomes an `attack-pattern`, a `grouping`, or another object type,
   and how a given report year is identified.
4. **Vocabularies are not enumerated.** `status`, `ownership`, `applicability`,
   `stack_components`, `lifecycle_relevance`, `implementation_type`,
   `capability_type`, `assessment_status`, and `assessment_type` show example
   values but have no defined open or closed vocabulary.
5. **Cardinality and optionality are unspecified**, beyond the STIX-required
   common properties (`type`, `spec_version`, `id`, `created`, `modified`).
6. **`score` semantics.** The range, scale, and meaning of
   `x-control-assessment.score` are undefined.
7. **`Control Type` is absent.** The charter's Control Data Model lists Control
   Type among a control's structured attributes; `x-control` has no equivalent
   property and the intended vocabulary is undefined. Charter terminology
   generally — it calls the field-level model the **Control Data Model (CDM)** — is
   not yet reconciled with the naming used here.
8. **Whether an SCC control and its source-framework controls are one object or
   two.** A unified catalog control harmonizing CCM CEK-03 and an AICM equivalent
   could be a distinct `x-control` in the `scc` namespace related by `csa-gap-mapping`, or
   the CCM object could simply gain SCC properties. The first keeps provenance
   clean; the second halves the object count. Note that carrying multiple framework
   versions weighs against the second: with CCM 4.0 and 4.1 both present as
   objects, "the CCM object gains SCC properties" has no single referent.

Unsettled conventions that bind all objects rather than a single type are tracked
in [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md#open-questions).

---

These objects allow the CSA Security Controls Catalog to be modeled, queried,
mapped, and audited in a standards-based, scalable fashion. They provide the basis
for integrating CSA-CC into broader STIX-based threat and risk modeling
ecosystems, and align with OSCAL and STIX semantic design principles.
