# Catalog objects

STIX objects committed as data. Each file holds one object, and its `id` is minted
once when the file is created and then fixed by being committed — the repository is
the identifier map, and git history is the audit trail.

**Generation must read existing objects and preserve their identifiers, never
re-mint.** STIX requires a UUIDv4 for SDO identifiers, which by construction cannot
be derived from content, so a generator that rebuilds from source and assigns fresh
UUIDs would silently break every reference a consumer holds — and every `maps-to`
relationship in the catalog itself.

## Layout

```
objects/<stix-type>/<secid-path>.json
```

Type first, then the source's SecID path within it:

```
objects/extension-definition/x-control.json
objects/identity/cloud-security-alliance.json
objects/x-control/cloudsecurityalliance.org/aicm/1.0/MDS-01.json
objects/x-regulation/europa.eu/ai-act/art-15-1.json
```

Human-readable paths rather than UUID filenames, so a pull request diff is
reviewable: a change to `MDS-01.json` is legible where a change to
`f47ac10b-….json` is not. The UUID lives in the object's `id`.

## Foundation objects

These are not catalog content. They are the objects that make catalog content
interpretable, and **they must travel with the content in every published bundle** —
a consumer cannot interpret an `x-control` without the definition that declares the
type, and cannot attribute it without the publisher identity.

### `extension-definition/`

One per custom type, declaring it as a new SDO and pointing at its JSON Schema in
[`../schemas/`](../schemas/). Every instance of a custom type references its
definition through `extensions`.

| Type | Definition identifier |
|---|---|
| `x-control` | `extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea` |
| `x-regulation` | `extension-definition--a72496a3-08f8-43fb-88c9-479bb94e5e02` |
| `x-control-implementation` | `extension-definition--1690104a-d3f2-4716-a334-252356f338dc` |
| `x-capability` | `extension-definition--43f8f73f-45e2-4d06-bdc0-46bdd5cb3e81` |
| `x-control-assessment` | `extension-definition--c2b74dc8-5ea7-4d9c-ade0-85474e5f70b4` |

### `identity/`

The publisher identity, `identity--51f9d480-d80b-4415-93c7-507cde4d1e85`. CSA-authored
objects point at it in `created_by_ref`.

Its `name` is the full organisation name, `Cloud Security Alliance`. STIX `identity`
has no short-code property, so short identifiers live in `external_references`
instead — the object carries its SecID and CSA's CVE Numbering Authority short name,
`CSAI`.

## These identifiers are permanent

Once published, consumers key off them. Changing one is a breaking change requiring a
migration path, not an edit. That is why they are minted deliberately and committed
rather than generated at publish time, and why there is one definition per type: a
breaking change to one type then leaves the other four untouched.

CI enforces that every identifier here also appears in
[`../SCHEMA-STIX-OBJECT-EXTENSIONS.md`](../SCHEMA-STIX-OBJECT-EXTENSIONS.md), so the
committed objects and the documented examples cannot drift into referencing different
definitions.

## Validating

```sh
python3 ../tools/validate.py <file>...     # custom types, against ../schemas/
```

Standard types — `identity`, `extension-definition`, `relationship` — are skipped by
that tool and checked by the OASIS validator instead. See
[`../schemas/README.md`](../schemas/README.md).
