---
title: "CSA Security Controls Catalog — STIX Modeling Conventions"
document-status: DRAFT
date: 2026-07-29
author: "CSA Security Controls Catalog working group"
status: "Provisional — open for discussion"
type: "Modeling conventions"
tags: [security-controls-catalog, stix, conventions, data-model]
---

# CSA Security Controls Catalog — STIX Modeling Conventions

## Purpose

This document records **how** the catalog uses STIX 2.1 — the modeling idioms,
invariants, and decision tests that apply to every object, present and future.

It is the middle of three documents, and the division is deliberate:

| Question | Document |
|---|---|
| **Why** STIX 2.1, and not OSCAL, CSAF, OSV, or RDF | [`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) |
| **How** we use STIX — conventions that bind all objects | this document |
| **What** properties each object carries | [`SCHEMA-STIX-OBJECT-EXTENSIONS.md`](SCHEMA-STIX-OBJECT-EXTENSIONS.md) |

The rationale answers a question that was settled once. The schema answers a
question about five specific types. This document answers the question that
recurs every time someone models something new — and that otherwise gets
re-litigated in each pull request.

Everything here is **provisional**, consistent with the catalog's exploratory /
research status. Conventions in the [Open questions](#open-questions) section are
explicitly *not* settled; do not treat a gap there as license to invent an answer
in instance data.

## 1. Relationships are SROs, not embedded reference arrays

Relationships between catalog objects are expressed with the standard STIX
`relationship` SRO. They are **not** encoded as arrays of identifiers inside the
objects themselves.

Three reasons, in order of weight:

**A mapping is a claim, and a claim needs its own properties.** Asserting that a
control corresponds to a regulatory clause carries rationale, scope
qualification, confidence, and authorship. An SRO holds those in `description`,
`confidence`, `created_by_ref`, and `external_references`. A bare identifier in a
string array holds none of them, so the reasoning behind every mapping would be
unrecordable — and mappings are the catalog's most contestable content. This
argument is independent of tooling: even with a perfect consumer, the string array
has nowhere to put the *why*.

**Generic STIX tooling can traverse an SRO; it cannot traverse a custom
property.** A TAXII server, CTI platform, or graph store already indexes
`source_ref` and `target_ref`. Nothing tells it that a custom `mappings` property
denotes an edge. Encoding edges in custom properties rebuilds, badly, the
relationship system STIX already provides — which is precisely the parallel
system this design set out to avoid.

**Independent versioning.** Adding, retracting, or revising one mapping becomes a
change to one relationship object rather than a modification of the control
itself. Controls stay stable while the contested claims about them churn
separately.

The cost is object count: a control mapped to twelve clauses becomes thirteen
objects rather than one. That is the ordinary STIX trade-off, and the ecosystem is
built for it.

### Constitutive references stay embedded

Not every embedded reference is a disguised relationship. STIX itself uses them
where the reference is **constitutive** of the object — `sighting.sighting_of_ref`,
`note.object_refs`, `malware-analysis.sample_ref`. The object has no meaning
without it, and the reference is not an independent assertion someone might
retract.

**The test:** if the reference can be added, revised, or withdrawn while the
object remains meaningful, it is a relationship. If removing it makes the object
incoherent, it is a property.

`x-control-assessment.assessed_control_ref` and `entity_ref` are the current
instance of the exception: an assessment with no assessed control and no assessed
entity is not an assessment. Converting them to SROs would be *more* invention,
not less, and would permit assessment objects to exist in an incoherent state.

## 2. Relationship types prefer the standard vocabulary

Use values from the STIX `relationship-type-ov` vocabulary where one fits —
`mitigates` for a control countering adversary behavior, for example. STIX permits
custom `relationship_type` strings, but *minimal invention* means a custom value
requires an explicit definition in the schema document, not casual coinage at
authoring time. An undocumented relationship type is indistinguishable from a
typo to every downstream consumer.

## 3. Identifiers

The STIX `id` property is `<type>--<UUIDv4>`, as the specification requires. No
alternative identifier scheme goes in `id`.

Catalog objects also carry a [SecID](https://secid.cloudsecurityalliance.org/) so
they resolve through SecID's public resolver. A `secid:` URI in `id` would be
invalid STIX and would break the maximum-compatibility principle, so **the SecID
goes in `external_references` with `source_name: "secid"` and the SecID string as
`external_id`.** That is the standard STIX place for an identifier assigned by
another system, so it needs no custom property — convention 4 stops at step 1.

**Object types follow SecID's type vocabulary** where a SecID type exists for the
concept, so the same distinctions hold in both systems — SecID classifies by what
an artifact *is*, not by who published it. Two SecID types are deliberately not
modeled as objects: `reference` and `methodology` are cited through
`external_references`, since a citation is what that property is for. Recording
the methodology a mapping was derived under belongs on the mapping relationship.

**SecID's registry is the current source for its own vocabulary.** Type tables in
this repository map catalog objects onto SecID types; they are not a maintained
copy of SecID's type list. Where the two disagree about what SecID contains, check
the resolver or its MCP server rather than trusting a table here.

**The two projects co-evolve, so divergence is not automatically a defect.** SecID
and this catalog work the same problem space from different angles, and neither is
subordinate to the other. `x-control-implementation` and `x-control-assessment`
have no SecID counterpart at present, while SecID covers ground the catalog does
not — those are places to learn from each other, and alignment may end up moving in
either direction. Where closer alignment is worth having, it is a deliberate change
carrying a migration path for anyone consuming published content, never an
automatic or pre-emptive rename.

**A questionnaire is a framework, not a new object type.** CAIQ questions are
`x-control` objects in a `*-caiq` framework, following SecID's own registration. The
`framework` property separates them from the controls they assess, so one object type
serves both and an `x-control-assessment` can assess a question without a schema
change — which is what makes a STAR submission, whose answers are per question,
representable at all.

**Third-party provenance is decomposed, not stored as one string.** An object
representing another publisher's content carries the components of its SecID as
separate queryable properties — namespace, name, version, and local identifier —
with the full SecID in `external_references`. A single opaque
`"secid:control/iso.org/27001@2022#A.8.24"` cannot answer "show me every CCM 4.1
control"; separate properties can. Version is optional, because many regulations
have none: GDPR is Regulation (EU) 2016/679, not a version number.

Human-facing control identifiers (`CEK-03` and similar) are content, not identity:
they belong in a dedicated property, never in `id`.

## 4. Standard properties before custom ones

Objects use the standard STIX common properties — `id`, `created`, `modified`,
`created_by_ref`, `labels`, `external_references`, `object_marking_refs` — and
introduce custom properties only where no standard property expresses the
concept.

`type`, `spec_version`, `id`, `created`, and `modified` are **required on every
SDO**, including the custom `x-*` types — they appear in the `required` array of
the OASIS STIX 2.1 JSON schema for core properties. `spec_version` **MUST be
`"2.1"`**; the schema's enum permits only `"2.0"` or `"2.1"`, and leaving it out
puts consumers in the position of inferring a version.

An object missing any of these is not valid STIX regardless of whether it is valid
JSON — a distinction worth keeping in mind, since syntax checking will not catch
it.

Before adding a custom property or a new `x-*` type, work down this list and stop
at the first hit:

1. Does a standard STIX common property already express it?
2. Does a standard SDO or SCO already express it, reachable by a `relationship`
   SRO?
3. Does a standard STIX vocabulary already enumerate the values?
4. Only then: define a custom property, and record why the three checks above
   failed.

A custom property that duplicates a standard one is a defect, not a convenience —
it splits the same fact across two representations and consumers will disagree
about which wins.

## 5. New object types are declared with extension-definition

New SDO types are declared using STIX 2.1's `extension-definition` mechanism, never
as bare `x-`-prefixed custom objects. The bare-custom-object approach is a STIX 2.0
convention that 2.1 deprecates — its custom-object section is titled "Custom
Objects (Deprecated)". Producers may still use it; the catalog does not, because
extension definitions are the preferred standardized path and give consumers a
retrievable definition rather than a name to guess from.

Each new type gets its own `extension-definition`, and every instance references it:

```json
"extensions": {
  "extension-definition--<UUID>": { "extension_type": "new-sdo" }
}
```

**One definition per type, not one shared across several.** Nothing in STIX
requires this — an instance carries its own `type`, so a shared definition would
still leave the types distinguishable. The reason is change isolation: definition
identifiers are permanent once published, so a shared definition couples the
stability of unrelated types together. Retiring or redefining one type should not
force a version bump on definitions for types that did not change, nor invalidate
references on objects of every other type. Per-type definitions also let each carry
its own `version` and a `schema` describing one type rather than an omnibus.

Two consequences bind anything that publishes catalog content. **The
extension-definition objects must travel with the instances**, because a consumer
cannot interpret an object without its definition. And **the identifiers are
permanent once published**: consumers key off them, so changing one is a breaking
change rather than an edit.

Standard STIX objects the catalog uses — `relationship`, `identity`,
`marking-definition` — are not extended and carry no `extensions` property.

The five definitions are minted and committed under
[`objects/extension-definition/`](objects/extension-definition/). Instance data
references those real identifiers; do not mint new ones.

### The publisher identity is fixed too

`created_by_ref` on CSA-authored objects points at the single committed CSA
`identity` in [`objects/identity/`](objects/identity/). Its identifier is permanent
for the same reason the definition identifiers are — consumers key off it — so it is
referenced, never re-created.

Its `name` is the full organisation name, `Cloud Security Alliance`. STIX `identity`
has no short-code property, so abbreviations have nowhere to live in the object;
where a short identifier is genuinely useful, such as CSA's CVE Numbering Authority
short name `CSAI`, it belongs in `external_references` alongside the SecID.

## 6. Every object carries TLP:WHITE

The catalog is public, so every published object carries the TLP:WHITE marking in
`object_marking_refs`:

```json
"object_marking_refs": ["marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"]
```

**TLP:WHITE is the STIX 2.1 spelling of what TLP 2.0 renamed TLP:CLEAR.** STIX 2.1
predefines exactly four TLP markings — WHITE, GREEN, AMBER, RED — with
specification-assigned identifiers, and forbids producers from defining their own
`tlp` markings. So there is no conformant `TLP:CLEAR` to use, and the identifier
above is a constant reproduced from the specification rather than one this project
minted. The marking object is committed at
[`objects/marking-definition/tlp-white.json`](objects/marking-definition/tlp-white.json)
verbatim, including its specification-fixed `created` timestamp.

**It has to be per object, because STIX offers nowhere else to put it.**
`object_marking_refs` is an object property, and a `bundle` is deliberately a
container with no semantics — there is no bundle-level or repository-level marking.
A statement in a README documents intent for humans but does not travel: an object
ingested into a CTI platform arrives carrying whatever is on the object and nothing
more.

Marking every object is therefore repetitive by necessity rather than by choice. It
is also cheap, since it is generated, and it removes a real ambiguity — an unmarked
object is not TLP:WHITE, it is *unspecified*, and some pipelines route or filter on
the presence of a marking.

Additional markings may accompany it; the schemas require that TLP:WHITE be present,
not that it be alone. A `marking-definition` object does not mark itself.

## 7. No changes to the wire format

Catalog objects are ordinary STIX 2.1 JSON. Nothing in this catalog changes the
STIX wire format, versioning model, or transport. If a design would require a
consumer to special-case the catalog before it can parse or route the data, the
design is wrong.

## 8. Lifecycle state and revocation are distinct

A custom property that duplicates a standard one is a defect (convention 4), but
two properties recording *different facts* are not duplicates — and lifecycle
state and revocation are different facts.

- **Lifecycle** is carried by the object's own status vocabulary: the catalog
  considers this object a draft, current, or no longer current.
- **`revoked: true`** is the standard STIX statement that the object is withdrawn
  as invalid — it should not have been published as it was.

Retiring content is not revoking it. STIX consumers routinely filter `revoked`
objects out entirely, so using `revoked` to mean "no longer current" silently
invalidates every historical assertion that references the object. Assessments,
mappings, and reports made while an object was current remain true statements
about the date they were made.

**Never express end-of-life with `revoked`.** Reserve `revoked` for content
published in error, and carry end-of-life in the lifecycle vocabulary.

Where one object replaces another, that is a relationship, not a
status value or a property — it is an assertion about two objects carrying its own
date and rationale, and the replaced object stays coherent without it. See
`SCHEMA-STIX-OBJECT-EXTENSIONS.md` § "`status`, `revoked`, and supersession" for
the applied case.

## 9. Reproducing external text

Most of what the catalog does with external standards is referential: citing a
clause by identifier, describing a requirement in original wording, asserting that
two requirements correspond. None of that reproduces a source's text, and none of
it is constrained here.

The constraint is narrow, and applies only to **verbatim text of a source carried
in catalog content** — `x-control.specification`, `x-regulation.text_excerpt`, and
anything similar.

Two axes govern it, and they are independent:

- **Redistribution** — may the text be reproduced at all?
- **Derivatives** — may it be modified, restructured, or paraphrased in place?

Both are recorded per source in the SecID datasets, alongside an SPDX identifier,
so this is a lookup rather than a judgment call. Consult the source's record rather
than reasoning from how short or well-attributed an excerpt is, and rather than
relying on a value quoted here — licence metadata belongs to the source record and
is corrected there.

Two cautions on using those records. Much of the licence metadata is
**bulk-generated**, and some records say so in their own notes; treat it as triage
rather than as permission, and verify before relying on it to authorise quoting a
source verbatim. And note the asymmetry in how the errors cost: a permissive source
mislabelled restrictive loses a citation, while a restrictive source mislabelled
permissive is a takedown. Only the second needs guarding, so where the record and
the publisher's own terms disagree, take the more restrictive reading.

### Citation-only sources

Where a publisher's terms do not permit reproduction, the object carries **only the
citation**: the standard number, and the clause identifier including its annex
prefix where the source has one. **No other text** — no title, no excerpt, no
paraphrase, no original description of what the clause says.

For ISO/IEC that means, for example, standard `42001`, version `2023`, identifier
`A.6.1.2`, and nothing else. `name` may hold a citation the catalog constructs from
those parts (`ISO/IEC 42001:2023 A.6.1.2`) so the object renders legibly in generic
STIX tools, since a citation is not the publisher's prose.

This is deliberately the same minimum that CCM and AICM already use when citing
these sources: it is the least data the catalog needs to express a mapping, and it
is what the rest of the field does.

**ISO/IEC text is not reproduced at any length.** ISO standards are not
redistributable, and CSA maintains a working relationship with ISO that this catalog
will not put at risk. The schemas enforce this for the `iso.org` and `iec.ch`
namespaces by rejecting `specification`, `description`, `implementation_guidance`,
and `audit_guidance` outright, so the rule cannot be broken by an oversight in
generation. That enforcement is a backstop for the case that is absolute, not a
substitute for checking a source's licence record — which remains the test for every
other publisher.

Referencing a clause by identifier is always available and is the default. See
`CONTRIBUTING.md` § "Sources and third-party content".

## Open questions

Unsettled conventions. Raise an issue rather than deciding any of these in
instance data.

1. **Whether relationship SROs carry their own SecID.** A mapping claim is catalog
   content too, so it may warrant an identifier of its own. Object placement is
   settled (see convention 3); this is only about the SROs.
2. **Data markings.** No convention exists for `object_marking_refs` or for a
   catalog `marking-definition` object. This matters because `LICENSE.txt`
   restricts what consumers may do with the published catalog, and a bundle
   ingested into a CTI platform arrives with no terms attached — the license is a
   file in this repository, and files do not travel with STIX objects. STIX's
   statement markings are the standard mechanism for conveying terms alongside
   data. Whether the catalog defines a CSA marking and applies it to every
   published object is a decision for the working group.
3. **`confidence` semantics.** STIX defines `confidence` as 0–100 and its
   appendix maps that range onto named scales. Catalog mapping SROs use
   `confidence`, but no scale has been adopted, so a value of 85 currently has no
   defined meaning. Note this is distinct from `x-control-assessment.score`,
   whose range and meaning are also undefined.
4. **`external_references` usage.** No convention for which `source_name` values
   are expected, or how framework citations, SecIDs, and documentation URLs are
   distinguished within the array.
5. **Bundle composition.** Whether the catalog publishes one bundle, a bundle per
   domain, or a bundle per object type; whether relationship SROs travel with
   their source objects; and how a tagged release maps onto bundle files.
6. **Object versioning in practice.** When a change bumps `modified` on an
   existing object versus creating a new object, and how consumers are expected
   to detect and reconcile catalog updates.
