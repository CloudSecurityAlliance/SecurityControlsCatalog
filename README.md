# CSA Security Controls Catalog

A canonical, machine-readable catalog of technology-agnostic security controls
and control metadata, maintained by the Cloud Security Alliance (CSA) Security
Controls Catalog (SCC) — a subgroup of CSA's
[**Compliance Automation Revolution (CAR)**](https://cloudsecurityalliance.org/research/working-groups/compliance-automation-revolution)
working group.

> **Status: early-stage / research-grade.** The data model and schemas in
> this repository are **exploratory and provisional** and may change as
> implementation experience accumulates. Treat the custom STIX extensions as
> research-status, not a stable specification. The AICM 1.1.0 controls, the
> AI-CAIQ 1.1.0 questions, and AICM's mappings to the EU AI Act, BSI, and ISO are
> committed under [`objects/`](objects/). Mapping coverage is partial: what could
> not be resolved from the source is recorded in [`quarantine/`](quarantine/)
> rather than guessed at.

## Why this exists

Organizations prove the same security controls over and over against overlapping
frameworks. The same encryption requirement is re-evidenced for ISO 27001, for
NIST 800-53, for a customer questionnaire, and for a regulator — each time by
hand, each time in a spreadsheet, each time as a point-in-time snapshot that is
stale the day after it is signed.

CAR exists to change that: to advance security and compliance automation and
continuous assurance through standardized, machine-readable approaches to
controls, assessments, and governance, reducing compliance burden while improving
consistency, transparency, and scalability.

Within CAR, the Security Controls Catalog is responsible for the **control layer**
— a canonical set of technology-agnostic controls and control metadata. Its focus
is control harmonization, regulatory mappings, machine-readable control formats,
and governance of control content, so that automation and interoperability are
possible across CSA frameworks and external standards.

Concretely, the catalog aims to let an organization define a control **once** and
have it linked to its mappings, implementation guidance, audit guidance, and
threat relevance — so evidence gathered once can answer many frameworks, and
assessment can move from static and periodic toward continuous.

## Relationship to CCM and AICM

The catalog **evolves and unifies** CSA's existing control frameworks — the Cloud
Controls Matrix (CCM) and the AI Controls Matrix (AICM) — rather than sitting
alongside them as a third framework. The CCM and AI Controls Framework working
groups were consolidated into the SCC, and AICM is the starting point for the
catalog's first version.

**CCM and AICM both remain supported.** CCM in particular has a large installed
base that will be in production use for years, and the catalog is being designed
so those users keep a first-class experience — including the spreadsheet and CAIQ
outputs they already depend on — rather than facing a forced migration. Adopting
the catalog is intended to be an upgrade path, not a cutover.

## What this is

The Security Controls Catalog expresses security controls — and their relationships to regulations,
implementations, capabilities, assessments, threats, and attack patterns — as a
graph, using **STIX 2.1** with a small set of custom STIX Domain Objects, declared
through STIX's standard `extension-definition` mechanism:

| Object | Role |
|---|---|
| `x-control` | A security control, from any publisher — CSA's own, CCM, AICM, ISO 27001, NIST 800-53, PCI DSS. CAIQ questions are controls too, in a `*-caiq` framework |
| `x-regulation` | A clause of binding law (GDPR, the EU AI Act, HIPAA) |
| `x-gap-mapping` | One control or regulation assessed against a **set** of targets elsewhere, with a `No Gap` / `Partial Gap` / `Full Gap` verdict |
| `x-control-implementation` | A technology-agnostic way of fulfilling a control |
| `x-capability` | A specific product or service feature that provides an implementation |
| `x-control-assessment` | The outcome of an assessment or audit against a control |

The types mirror [SecID](https://secid.cloudsecurityalliance.org/)'s vocabulary,
which classifies by what an artifact *is* rather than who published it — so another
framework's controls are controls, and only legally binding requirements are
regulations.

These connect to each other and to the wider STIX graph (including MITRE
ATT&CK) through standard STIX relationships, so the data flows unchanged
through existing STIX/TAXII tools, CTI platforms, and graph stores.

The catalog is designed to **interoperate with — not replace — OSCAL**, and to
align with CSA's wider control and assurance work, including STAR/CAIQ and IoT
security.

## What's in the catalog

<!-- coverage:summary:start -->
| STIX type | Objects |
|---|---|
| `x-control` | 987 |
| `x-gap-mapping` | 423 |
| `relationship` | 320 |
| `x-regulation` | 106 |
| `extension-definition` | 7 |
| `identity` | 1 |
| `marking-definition` | 1 |
| **Total** | **1845** |
<!-- coverage:summary:end -->

Objects are committed one per file under `objects/<stix-type>/<secid-path>.json`, so
a diff is reviewable and every object has a stable path:

```
objects/x-control/cloudsecurityalliance.org/aicm/1.1.0/MDS-01.json
objects/x-control/cloudsecurityalliance.org/aicm-caiq/1.1.0/MDS-01.1.json
objects/x-control/iso.org/27001/2022/A.5.1.json
objects/x-regulation/europa.eu/ai-act/art-17.1.a.json
objects/x-gap-mapping/cloudsecurityalliance.org/aicm/1.1.0/ai-act/MDS-01.json
```

Everything is generated from published source releases by the scripts in
[`tools/`](tools/) and committed rather than built at publish time, because the
identifiers have to be stable across releases. The generators are idempotent: run one
against an unchanged source and it writes nothing; run it against a corrected source
and the diff is exactly what the correction touched.

**Mapping coverage is partial, and the gap is documented rather than hidden.** A
reference that cannot be resolved to a specific control in a specific standard is held
back instead of guessed at, because a guessed reference becomes a permanent identifier.
Everything withheld is listed per control, in the publisher's own strings, under
[`quarantine/`](quarantine/).

### Reading and correcting an object without reading STIX

Committed objects are STIX JSON, which is what consumers need and not what a person
should have to read to check whether a control's audit guidance is right. `tools/yaml_view.py`
renders any object as YAML with the machinery removed, and takes an edited rendering
back to the exact JSON:

```sh
pip install pyyaml
python3 tools/yaml_view.py objects/x-control/cloudsecurityalliance.org/aicm/1.1.0/MDS-01.json
python3 tools/yaml_view.py --write edited.yaml     # writes the JSON object back
python3 tools/yaml_view.py --check                 # round-trips every committed object
```

The view withholds only the properties that were never authored by hand — the
identifier, the timestamps, the TLP marking, the publisher identity, the extension
reference — and restores them from the committed object, so an edit changes the property
you edited and `modified`, and nothing else. `--check` requires the round trip to be
byte-identical for every object in the catalog and runs in CI, because a view that
silently loses a carriage return in a publisher's text would be worse than no view.

It corrects committed objects; it does not author new ones. Identifiers are minted once,
and catalog content comes from published source releases through the generators in
[`tools/`](tools/). Reasoning: see
[`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) § "Why the
committed form is JSON".

### Checking it yourself

```sh
pip install jsonschema
python3 tools/validate.py --self-test                     # the schemas
find objects -name '*.json' | xargs python3 tools/validate.py
python3 tools/coverage.py                                 # what is here, counted
```

Full STIX 2.1 conformance needs the OASIS validator, installed from a recursive clone
rather than PyPI — the published wheel omits its bundled schemas:

```sh
git clone --recursive https://github.com/oasis-open/cti-stix-validator.git
pip install -e cti-stix-validator
find objects -name '*.json' | xargs python3 -m stix2validator.scripts.stix2_validator \
  --schemas ./schemas/ --enforce-refs --disable 302
```

CI runs both on every pull request, plus checks that each object agrees with its own
path and SecID, that every reference resolves to a committed object, and that nothing
held in quarantine was also published. See
[`.github/workflows/validate.yml`](.github/workflows/validate.yml).

## How the custom types are declared

The custom types are declared through STIX 2.1's standard `extension-definition`
mechanism, not by convention on the `type` string. Each has a published definition
object pointing at a machine-readable JSON Schema, and every instance references its
definition. Two things follow that matter if you consume the catalog:

**These identifiers are stable and you can rely on them.** They are minted once and
permanent — changing one would be a breaking change requiring a migration path, not
an edit.

| Type | Definition identifier |
|---|---|
| `x-control` | `extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea` |
| `x-regulation` | `extension-definition--a72496a3-08f8-43fb-88c9-479bb94e5e02` |
| `x-control-implementation` | `extension-definition--1690104a-d3f2-4716-a334-252356f338dc` |
| `x-capability` | `extension-definition--43f8f73f-45e2-4d06-bdc0-46bdd5cb3e81` |
| `x-control-assessment` | `extension-definition--c2b74dc8-5ea7-4d9c-ade0-85474e5f70b4` |
| `x-gap-mapping` | `extension-definition--b1d89841-2dc0-4559-af18-380ecd4c1682` |

**A published bundle carries its own definitions.** They travel with the content, so
an unfamiliar consumer can retrieve what `x-control` means from the `schema` property
rather than guessing from the name — and two producers who both happen to emit
`x-control` stay distinguishable by the definition their objects reference.

The definition objects and the CSA publisher identity live in
[`objects/`](objects/); their schemas are in [`schemas/`](schemas/), and
[`tools/validate.py`](tools/) checks objects against them.

## Data markings

Everything in this repository is **TLP:CLEAR** — it is a public repository and the
catalog is published for open consumption.

In the data itself that is expressed as **TLP:WHITE**, which is the STIX 2.1 spelling
of the same thing: STIX 2.1 predefines four TLP markings and forbids producers from
minting their own, and TLP 2.0's rename to CLEAR postdates it. Every object carries
it in `object_marking_refs`, because STIX has no bundle-level or repository-level
marking — a statement here documents intent, but only a property on the object
travels with it.

## Design documentation

Three documents describe the data model, divided by the question each answers:

| Question | Document |
|---|---|
| **Why** STIX 2.1 — and not OSCAL, CSAF, OSV, or RDF | [`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md) |
| **How** the catalog uses STIX — modeling conventions binding all objects | [`CONVENTIONS-STIX-MODELING.md`](CONVENTIONS-STIX-MODELING.md) |
| **What** each object carries — field-level schemas | [`SCHEMA-STIX-OBJECT-EXTENSIONS.md`](SCHEMA-STIX-OBJECT-EXTENSIONS.md) |

All three are drafts. The conventions and schema documents each end with an
**Open questions** section recording what is deliberately not yet decided —
worth reading before building against the model.

## Who it's for

Cloud security and GRC practitioners, framework and tool builders, auditors,
and AI agents that need controls and their cross-framework mappings in a
structured, queryable form.

## Intended publication formats

STIX 2.1 (the back-end representation), OSCAL (for compliance and audit
consumers), plain JSON, YAML, and **Excel and CSV**. Spreadsheets are a
first-class output, not an afterthought — they are what much of the existing CCM
audience already works in. See the design rationale for the reasoning.

## Using the catalog

The repository is the distribution channel — clone it, or consume tagged
releases.

Catalog objects carry a [SecID](https://secid.cloudsecurityalliance.org/) in their
`external_references`, so they can be resolved through SecID's public resolver.
This is design intent rather than shipped fact — no catalog content has been
published yet — but the placement is settled, and the schema examples follow it.

## Contributing

Contributions are welcome by fork and pull request. **All contributions
require a signed Contributor License Agreement (CLA)** — you sign the **current
CLA version** once for this project (re-signing only if the CLA materially
changes), by opening a pull request adding a signature file (containing the full
CLA text you agree to) to the CSA CLA-Ledger. It lets CSA include your
work in the catalog and CSA's broader offerings while you keep ownership of your
contribution. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how it works and what
signing means.

## Working group

The Security Controls Catalog operates as a subgroup of CSA's
[Compliance Automation Revolution (CAR)](https://cloudsecurityalliance.org/research/working-groups/compliance-automation-revolution)
working group. Its mission, scope, and governance are set out in the
[SCC Working Group 2026 Charter](https://cloudsecurityalliance.org/artifacts/scc-wg-2026-charter).

Working group information and how to participate:
<https://cloudsecurityalliance.org/research/working-groups/security-controls-catalog>.

## License

The published catalog is governed by [`LICENSE.txt`](LICENSE.txt). Note that
the license that governs *consuming* the published catalog and the CLA that
governs *contributing* to it are two different things — see `CONTRIBUTING.md`.
