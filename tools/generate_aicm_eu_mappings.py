#!/usr/bin/env python3
"""Generate EU AI Act provisions and AICM's gap mappings to them.

Run against the AICM JSON distribution, after its controls have been generated:

    python3 tools/generate_aicm_eu_mappings.py path/to/aicm-1.1.0.json

Emits x-regulation objects for each cited provision, and one x-gap-mapping per
control carrying AICM's coverage verdict over the set of provisions it names.

Nothing is normalised. A reference is converted only if it already parses under
the citation grammar below; anything else is quarantined with its control, and the
quarantine is written out as data rather than left as a count in a log. The catalog
does not tidy a publisher's data in transit — see CONVENTIONS-STIX-MODELING.md
section 10 — and here the argument is sharper than for prose, because a guessed
reference becomes a permanent identifier that consumers key off.

Quarantine is per control, not per reference. A gap verdict is assessed against the
whole set of provisions, so dropping one target and keeping the verdict would not
publish an incomplete claim but a false one: No Gap over four of five provisions
asserts something AICM never assessed. A control with any unparseable reference is
therefore held back entirely.
"""

import argparse
import datetime
import json
import pathlib
import re
import sys
import uuid

from catalog import CSA_IDENTITY, NAMESPACE, TLP_WHITE, emit, order, report

REGULATION_EXT = "extension-definition--a72496a3-08f8-43fb-88c9-479bb94e5e02"
MAPPING_EXT = "extension-definition--b1d89841-2dc0-4559-af18-380ecd4c1682"

COLUMN = "eu_ai_act"
REG_NAMESPACE = "europa.eu"
REGULATION = "ai-act"
PUBLICATION_ID = "Regulation (EU) 2024/1689"
EURLEX = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
JURISDICTION = "EU"

# The publisher's way of saying there is nothing to point at. It is not a
# reference and does not become a target; a control whose only entry is this gets
# no mapping object, since STIX has no empty target set to give it.
NO_MAPPING = "no mapping"

# The citation grammar. Deliberately strict: it accepts the forms the source
# already uses consistently and nothing else. Article and annex subpaths follow
# the shape SecID registers for EU instruments, extended to paragraphs and points
# because the registry has no pattern for those yet.
GRAMMAR = [
    (re.compile(r"^Article (\d+)((?: \(\d+\))*(?: \([a-z]\))*)$"), "art"),
    (re.compile(r"^Recital (\d+)()$"), "recital"),
    (re.compile(r"^Annex ([IVX]+)()$"), "annex"),
]
PART = re.compile(r"\(([0-9a-z]+)\)")


def clause_identifier(line):
    """The SecID subpath for a reference, or None if it does not parse."""
    for pattern, prefix in GRAMMAR:
        m = pattern.match(line)
        if m:
            parts = PART.findall(m.group(2))
            return ".".join([f"{prefix}-{m.group(1)}", *parts])
    return None


def citation(clause):
    """A human-readable citation, built from the identifier rather than the source.

    The provision's title is not carried. AICM records some titles inline and most
    not at all, in three different casings, and inventing the rest would put words
    in the legislator's mouth. The identifier is the reference.
    """
    head, *parts = clause.split(".")
    kind, number = head.split("-", 1)
    label = {"art": "Article", "recital": "Recital", "annex": "Annex"}[kind]
    suffix = "".join(f"({p})" for p in parts)
    return f"EU AI Act {label} {number}{suffix}"


def build_regulation(clause, now):
    return order({
        "type": "x-regulation",
        "spec_version": "2.1",
        "id": f"x-regulation--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {REGULATION_EXT: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        "name": citation(clause),
        "regulation_namespace": REG_NAMESPACE,
        "regulation": REGULATION,
        "clause_identifier": clause,
        "publication_id": PUBLICATION_ID,
        "jurisdiction": JURISDICTION,
        "external_references": [
            {"source_name": "secid",
             "external_id": f"secid:regulation/{REG_NAMESPACE}/{REGULATION}#{clause}"},
            {"source_name": "EUR-Lex", "url": EURLEX},
        ],
    }, [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "extensions", "created_by_ref", "name", "regulation_namespace",
        "regulation", "clause_identifier", "publication_id", "jurisdiction",
        "external_references",
    ])


def build_mapping(source_ref, target_refs, gap_level, addendum, published, now):
    obj = {
        "type": "x-gap-mapping",
        "spec_version": "2.1",
        "id": f"x-gap-mapping--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {MAPPING_EXT: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        "source_ref": source_ref,
        "target_refs": target_refs,
        "gap_level": gap_level,
        "valid_from": published,
    }
    if addendum and addendum.strip():
        obj["description"] = addendum
    return order(obj, [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "extensions", "created_by_ref", "source_ref", "target_refs", "gap_level",
        "description", "valid_from",
    ])


def read_column(controls):
    """Split each control's mapping cell into parsed and unparsed references."""
    for c in controls:
        cell = c["scope_applicability_mappings"][COLUMN]
        lines = [l.strip() for l in (cell["control_mapping"] or "").split("\n")
                 if l.strip()]
        real = [l for l in lines if l.lower() != NO_MAPPING]
        parsed = {l: clause_identifier(l) for l in real}
        yield c["control_id"], cell, real, parsed


def committed_controls(objects, version):
    root = (pathlib.Path(objects) / "x-control" / NAMESPACE / "aicm" / version)
    if not root.is_dir():
        sys.exit(f"no committed aicm {version} controls at {root}; generate them first")
    return {json.loads(p.read_text())["control_identifier"]: json.loads(p.read_text())["id"]
            for p in sorted(root.glob("*.json"))}


def self_test():
    cases = [
        ("Article 17", "art-17"),
        ("Article 17 (1)", "art-17.1"),
        ("Article 17 (1) (a)", "art-17.1.a"),
        ("Article 16 (c)", "art-16.c"),
        ("Recital 81", "recital-81"),
        ("Annex IV", "annex-IV"),
        # Everything below is held back rather than guessed at. Each is a real
        # string from AICM 1.1.0.
        ("No Mapping", None),
        ("Article 14", None),            # narrow no-break space, looks correct
        ("Article 17,", None),                # trailing comma
        ("Article 13(1)", None),              # missing space
        ("Article 17 (1[g])", None),          # square brackets for a point
        ("Article 9 (Risk Management)", None),   # title embedded
        ("Recital 69, page 20/144", None),    # page number of a PDF rendering
        ("Article 53 and Annex XI", None),    # two provisions on one line
        ("Annex VII 5.3", None),              # annex sub-numbering, second spelling
        ("Annex IV (2) (g) (3) (9)", None),   # nesting genuinely ambiguous
        ("Article(s) 16 to 27 (Section 3)", None),
    ]
    bad = 0
    for line, want in cases:
        got = clause_identifier(line)
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {line!r} -> {got!r}")
        if not ok:
            print(f"       expected {want!r}")
    for clause, want in [("art-17.1.a", "EU AI Act Article 17(1)(a)"),
                         ("annex-IV", "EU AI Act Annex IV"),
                         ("recital-81", "EU AI Act Recital 81")]:
        got = citation(clause)
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} citation({clause!r}) -> {got!r}")
    total = len(cases) + 3
    print(f"\n{total - bad}/{total} generator self-tests passed")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", help="the AICM JSON distribution")
    ap.add_argument("--out", default="objects")
    ap.add_argument("--quarantine", default="quarantine")
    ap.add_argument("--now")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.source:
        ap.error("a source is required unless --self-test is given")

    now = args.now or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    data = json.loads(pathlib.Path(args.source).read_text())
    version = data["specification_version"]
    published = f"{data['published']}T00:00:00.000Z"
    controls = committed_controls(args.out, version)

    clean, held, clauses = [], [], set()
    for cid, cell, real, parsed in read_column(data["controls"]):
        if not real:
            continue                      # No Mapping: nothing to point at
        if all(parsed.values()):
            clean.append((cid, cell, [parsed[l] for l in real]))
            clauses.update(parsed.values())
        else:
            held.append({
                "control": cid,
                "gap_level": cell["gap_level"],
                "unparsed": [l for l in real if not parsed[l]],
                "parsed": [l for l in real if parsed[l]],
            })

    reg_root = pathlib.Path(args.out) / "x-regulation" / REG_NAMESPACE / REGULATION
    reg_tally = emit((reg_root / f"{c}.json", build_regulation(c, now))
                     for c in sorted(clauses))
    report(f"{REGULATION} provisions", reg_root, reg_tally)

    reg_ids = {c: json.loads((reg_root / f"{c}.json").read_text())["id"]
               for c in sorted(clauses)}
    map_root = (pathlib.Path(args.out) / "x-gap-mapping" / NAMESPACE / "aicm"
                / version / REGULATION)
    map_tally = emit((map_root / f"{cid}.json",
                      build_mapping(controls[cid], [reg_ids[c] for c in targets],
                                    cell["gap_level"], cell["addendum"],
                                    published, now))
                     for cid, cell, targets in clean)
    report(f"aicm {version} -> {REGULATION} mappings", map_root, map_tally)

    qpath = pathlib.Path(args.quarantine) / f"aicm-{version}-{REGULATION}.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(json.dumps({
        "source": f"AICM {version}, scope_applicability_mappings.{COLUMN}",
        "mappings": str(map_root),
        "why": "These references do not parse under the catalog's citation grammar. "
               "They are held back rather than normalised, because a guessed "
               "reference becomes a permanent identifier. Quarantine is per control: "
               "a gap verdict is assessed against the whole set of provisions, so "
               "publishing it over a subset would assert something the publisher "
               "never assessed.",
        "controls_mapped": len(clean),
        "controls_held": len(held),
        "references_unparsed": sum(len(h["unparsed"]) for h in held),
        "entries": sorted(held, key=lambda h: h["control"]),
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"\nquarantine -> {qpath}")
    print(f"  {len(clean)} controls mapped, {len(held)} held "
          f"({sum(len(h['unparsed']) for h in held)} unparsed references)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
