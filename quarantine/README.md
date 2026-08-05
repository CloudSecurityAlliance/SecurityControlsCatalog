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

## What is *not* in here, and why that distinction matters

A quarantine file lists what could not be converted. It is not a defect list, and
conflating the two is the failure mode this section exists to prevent.

An unfamiliar convention is indistinguishable from a mistake to a parser that does
not know it. An early pass over the ISO column reported nineteen references as
"no standard named" — they were the same reference with the standard written at the
end of the line instead of the start, used consistently across a whole domain. That
was a gap in the parser reported as a gap in the data, and it was published as a
defect report before anyone noticed.

**Consistency is the signature of a convention.** A shape that repeats across a
domain is house style; a shape that appears once is a typo. Before anything here is
described to a publisher as an error, cluster it: repeated shapes get a question
("is this a convention we should support?"), singletons get a defect report.

Each file therefore carries a `not_errors` section for things the conversion drops
or holds that are **not** the publisher's fault:

- **`scoped_no_mapping_dropped`** — cells stating that one named standard has no
  mapping while others in the same cell do. That is a per-standard verdict, and an
  `x-gap-mapping` carries one verdict for the whole target set, so it cannot be
  represented. A modelling gap on this side, recorded rather than silently lost.
- **`continuation_lines_held`** — a bare clause following a line that named a
  standard, which reads as continuing it. Held rather than converted because it is
  inferred from position rather than stated on the line. Confirm the convention and
  these convert with no other change.

## Files

<!-- coverage:files:start -->
| File | Source column | Mapped | Held |
|---|---|---|---|
| [`aicm-1.1.0-ai-act.json`](aicm-1.1.0-ai-act.json) | `eu_ai_act` | 123 | **40** |
| [`aicm-1.1.0-bsi-ai-c4.json`](aicm-1.1.0-bsi-ai-c4.json) | `bsi_ai_c4` | 119 | **125** |
| [`aicm-1.1.0-iso.json`](aicm-1.1.0-iso.json) | `iso_iec_42001_2023` | 181 | **63** |
<!-- coverage:files:end -->

The BSI column is the worst of the three, and for a different reason than the others.
It is not formatting: 288 of its 692 lines carry a bare control code with no standard
attached, in a column whose two standards number their controls in overlapping ways.
Nothing in those rows says which standard is meant.

Each column's open questions are filed separately:
[#16](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/16)
(BSI attribution),
[#18](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/18)
(EU AI Act citation form),
[#17](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/17)
and [#26](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/26)
(ISO editions and column contents),
[#27](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/27)
(text artefacts), and
[#28](https://github.com/CloudSecurityAlliance/SecurityControlsCatalog/issues/28)
(per-standard verdicts).

When a release resolves one, re-running the generator moves the affected controls
out of quarantine and into the catalog, and both changes appear in the same diff.
