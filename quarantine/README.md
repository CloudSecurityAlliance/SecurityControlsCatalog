# Quarantine

Source data the catalog could not convert, recorded as data rather than dropped.

Each file lists what a generator held back from one source column, why, and the
exact strings involved. It is written by the generator on every run, and CI fails if
a committed file and a fresh run disagree — so coverage cannot change without the
change appearing in a diff.

## Why hold anything back

Catalog identifiers are permanent. A reference converted by guesswork becomes an
object that consumers key off, and correcting it later is a migration rather than an
edit. Where a source's reference does not parse under the catalog's citation
grammar, it is held back instead of normalised — the same rule that keeps reproduced
text exactly as published, applied to references, where the cost of being wrong is
higher because the result is an identifier rather than a sentence.

Errors are raised with the publisher, and the quarantine is the artifact to raise
them with: it is the complete list, in the publisher's own strings, of what could not
be read.

## Quarantine is per claim, not per reference

A gap mapping carries one verdict over a **set** of targets, and the set is
constitutive of the claim — remove a target and `No Gap` may no longer hold. So a
control with one unreadable reference is held back entirely rather than published
over the targets that did parse. Publishing the subset would not be an incomplete
claim but a false one: it would assert a verdict the publisher never gave over that
set.

This is why an entry lists `parsed` alongside `unparsed`. The parsed references are
not missing from the catalog by accident; they are withheld because their claim
cannot be stated without the rest.

## What the counts mean

| Field | Meaning |
|---|---|
| `controls_mapped` | claims published from this column |
| `controls_held` | claims withheld because at least one reference did not parse |
| `references_unparsed` | individual strings that did not parse |

`controls_held` is the number that matters for coverage. `references_unparsed` is
the number that matters for cleanup, and is usually larger, since one control can
carry several unreadable references.

## Files

| File | Source column | Held |
|---|---|---|
| `aicm-1.1.0-ai-act.json` | AICM 1.1.0 `scope_applicability_mappings.eu_ai_act` | 40 of 163 controls |

Filed with the publisher as
[issue #18](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/18).
When a release fixes a reference, re-running the generator moves it out of
quarantine and into the catalog, and both changes show up together.
