# JSON Schemas for the CSA-CC custom STIX types

Machine-readable schemas for the five custom STIX 2.1 object types. These are the
`schema` targets referenced by each type's `extension-definition` object, and they
are what a validator checks instance data against.

The narrative definitions — what each property *means*, and why the model is shaped
this way — are in
[`../SCHEMA-STIX-OBJECT-EXTENSIONS.md`](../SCHEMA-STIX-OBJECT-EXTENSIONS.md).
Where the two disagree, that document is authoritative and this directory has a bug.

| Schema | Type |
|---|---|
| `x-control.json` | A security control, from any publisher |
| `x-regulation.json` | A clause of legally binding law |
| `x-control-implementation.json` | A technology-agnostic implementation approach |
| `x-capability.json` | A specific product or service security feature |
| `x-control-assessment.json` | An assessment outcome |
| `csa-gap-mapping.json` | A CSA gap mapping — a `relationship` with CSA's coverage verdict |
| `derived-from.json` | A standard `derived-from` relationship, as used for CAIQ question to control |

## Validating

Standalone, against these schemas only:

```sh
python3 tools/validate.py path/to/bundle.json
```

Full STIX 2.1 conformance plus these schemas, using the OASIS validator:

```sh
git clone --recursive https://github.com/oasis-open/cti-stix-validator.git
pip install -e cti-stix-validator
stix2_validator --schemas ./schemas/ --enforce-refs path/to/bundle.json
```

`--schemas` validates input against a custom directory *in addition to* the STIX
schemas bundled with the validator, so core STIX requirements and catalog-specific
field rules are both checked. `--enforce-refs` catches SRO references to objects
missing from the bundle.

## Scope, and what these deliberately do not do

**They validate what is settled, and stay quiet about what isn't.** Only the
STIX-required common properties plus `extensions` are required — and, on
`x-control-assessment`, the two constitutive references. Everything else is
optional, because per-property optionality is an open question in the narrative
document. A schema that guessed would silently settle it.

**`additionalProperties` is not restricted.** The model is research-grade and STIX
permits custom properties, so an unknown property is not an error yet. The trade-off
is that typos pass. Worth tightening once the model stabilises.

**Vocabularies are mostly unconstrained.** `status` is an enum because its values are
settled. `ownership`, `applicability`, `stack_components`, `implementation_type`,
and `capability_type` are open string arrays, while `assessment_status` and
`assessment_type` are open strings,
pending a vocabulary decision.

**One boundary is enforced structurally.** `x-control-implementation` rejects
`platform`, `product`, `vendor_namespace`, and `config_snippet`. Those belong to
`x-capability`, and an implementation approach carrying them has drifted into being
a capability — the conflation the two types exist to prevent.

**One schema covers a standard type.** `csa-gap-mapping.json` validates
`relationship` objects whose `relationship_type` is `csa-gap-mapping`.
`tools/validate.py` dispatches on `relationship_type` for relationships, so a plain
`mitigates` edge is left to the OASIS validator while a CSA mapping is checked here.
Its custom properties are declared by a `toplevel-property-extension`, since
`relationship` is a standard STIX type and an undeclared property on it could collide
with another producer's.

**Every object must carry TLP:WHITE.** `object_marking_refs` is required and must
contain the specification-assigned TLP:WHITE identifier. Additional markings are
allowed; the requirement is that it be present, not that it be alone.

**Cross-object rules are out of reach.** JSON Schema validates one object at a time,
so it cannot check that an `extension-definition` travels with the instances
referencing it, that a licence-constrained field matches the source's recorded
terms, or that `revoked` was not used to mean retired. Those need bundle-level
checks.
