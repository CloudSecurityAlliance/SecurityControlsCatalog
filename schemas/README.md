# JSON Schemas for the CSA-CC custom STIX types

Machine-readable schemas for the catalog's custom STIX 2.1 object types. These are the
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
| `x-gap-mapping.json` | A CSA gap mapping — one source assessed against a set of targets |
| `derived-from.json` | A standard `derived-from` relationship, as used for CAIQ question to control |
| `superseded-by.json` | A newer object replacing an older one |

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

**`additionalProperties` is not restricted, and tightening it here would be the wrong
fix.** The model is research-grade and STIX 2.1 permits custom properties, so an
unknown property is not an error in a *published contract* — setting
`additionalProperties: false` would make these schemas stricter than STIX and reject a
consumer's legitimate extension, which is the maximum-compatibility principle failing
in the other direction.

The trade-off it buys is that a typo passes: `speification` instead of `specification`
silently drops the specification text and every per-object check reports no problem,
because there is nothing to compare one object against. That is mitigated where it can
be, without touching the contract — **CI holds what the catalog itself commits to the
properties these schemas define**, since what a consumer may add and what the catalog
may publish are different questions and only the second is ours to enforce. See
[`../.github/workflows/validate.yml`](../.github/workflows/validate.yml).

**Vocabularies are mostly unconstrained, on purpose.** `status` and `gap_level` are
enums because their values are settled. Everything else is open — `control_type`,
`threat_category`, `stack_components`, `implementation_type`, `capability_type`,
`assessment_status`, `assessment_type`, and the role, layer, and phase keys inside the
guidance and applicability objects — because the frameworks disagree: AICM uses six
responsibility roles where CCM uses three, and their threat taxonomies differ.
Enumerating any of them would lock the property to a single framework.

**Property names and shapes follow the published source data.** Guidance is an object
keyed by responsible role rather than a string, because that is how the frameworks
express shared responsibility. `typical_control_applicability_and_ownership` is one
object rather than separate applicability and ownership properties, because ownership
varies by architectural layer and the pairing is the information. Boolean maps in the
source become arrays of the keys that apply, which is lossless and easier to filter;
non-boolean maps stay objects, because flattening them would lose the pairing.

**One boundary is enforced structurally.** `x-control-implementation` rejects
`platform`, `product`, `vendor_namespace`, and `config_snippet`. Those belong to
`x-capability`, and an implementation approach carrying them has drifted into being
a capability — the conflation the boundary exists to prevent.

**Two schemas cover a standard type.** `derived-from.json` and `superseded-by.json`
validate `relationship` objects by their `relationship_type`; `tools/validate.py`
dispatches on that property, so a relationship the catalog does not define is left to
the OASIS validator. Neither adds custom properties, so neither needs an extension
declaration.

**Every object must carry TLP:WHITE.** `object_marking_refs` is required and must
contain the specification-assigned TLP:WHITE identifier. Additional markings are
allowed; the requirement is that it be present, not that it be alone.

**Cross-object rules are out of reach.** JSON Schema validates one object at a time,
so it cannot check that an `extension-definition` travels with the instances
referencing it, that a licence-constrained field matches the source's recorded
terms, or that `revoked` was not used to mean retired. Those need bundle-level
checks.
