#!/usr/bin/env python3
"""Generate AICM's gap mappings to BSI and ISO standards, and the targets they cite.

Run against the AICM JSON distribution, after its controls have been generated:

    python3 tools/generate_aicm_standard_mappings.py path/to/aicm-1.1.0.json

Covers two columns, which behave the same way and differ only in citation grammar:
bsi_ai_c4 and iso_iec_42001_2023. Targets become citation-only x-control objects —
another publisher's controls are controls — and each source control gets one
x-gap-mapping carrying AICM's verdict over the set it names.

Both columns carry more than one standard. bsi_ai_c4 cites BSI AIC4 and BSI C5;
iso_iec_42001_2023 cites ISO/IEC 42001, 27001, and 27002. The targets are minted
under whichever standard they name, because the verdict is asserted over the whole
set: dropping the targets that fall outside the column's title and keeping the
verdict would assert a coverage claim the publisher never made. The column names
are wrong, which is a data-quality issue to raise, not a reason to publish a
narrower claim than was assessed.

No text is carried from any target. AICM records clause titles inline for ISO, and
those are ISO's words: the schemas reject prose on iso.org objects outright, so
these objects hold a standard number, a clause identifier, and a citation the
catalog constructs. The titles are also unreliable — the source gives 104 clauses
more than one title — but the licence is the binding reason, not the quality.
"""

import argparse
import datetime
import json
import pathlib
import re
import sys
import uuid

from catalog import CONTROL_EXT, CSA_IDENTITY, NAMESPACE, TLP_WHITE, emit, order, report

MAPPING_EXT = "extension-definition--b1d89841-2dc0-4559-af18-380ecd4c1682"

CONTROL_KEYS = [
    "type", "spec_version", "id", "created", "modified", "object_marking_refs",
    "extensions", "created_by_ref", "name", "framework_namespace", "framework",
    "framework_version", "control_identifier", "status", "external_references",
]
MAPPING_KEYS = [
    "type", "spec_version", "id", "created", "modified", "object_marking_refs",
    "extensions", "created_by_ref", "source_ref", "target_refs", "gap_level",
    "description", "valid_from",
]

# Sentinels. Both columns use several spellings, and the ISO column scopes one to a
# single standard ("No Mapping for ISO 42001") inside a cell that still cites others.
# None is a reference; a cell holding only sentinels yields no mapping object at all.
SENTINEL = re.compile(
    r"^(no mapping( for iso 42001)?|no iso 42001 mapping\.?|not applicable|n/a)$", re.I)

BSI = re.compile(r"^C(4|5) ([A-Z]{2,4}-\d{2})$")
ISO = re.compile(r"^(?:ISO/IEC |ISO )?(42001|27001|27002)(?::(20\d\d))?\s*[:\-–]?\s*"
                 r"((?:A|B)\.\d+(?:\.\d+)*|\d+(?:\.\d+)+)(?:\s+\S.*)?$")

# A second clause hiding in the trailing text. The tail is normally a title, which
# is discarded, but some lines join two provisions with "and" or a slash. Matching
# only the first would publish a mapping short one target, which is the exact
# falsification this design exists to prevent, so the whole line is rejected.
SECOND_CLAUSE = re.compile(r"(?<![\w.])(?:A|B)\.\d+(?:\.\d+)*(?![\w.])"
                           r"|(?<!\d)(?:42001|27001|27002)(?!\d)")


def bsi_target(line):
    """BSI AIC4 and C5 targets. An unprefixed code is not resolvable.

    288 of 692 lines in this column carry a bare code with no standard. Of the 103
    distinct codes, 47 also appear elsewhere as C5 and 23 as C4, two appear as both,
    and 35 appear as neither — so even the ones that look inferable are inferred from
    where the same string happens to appear in other rows, not from anything the row
    says. None is converted.
    """
    m = BSI.match(line)
    if not m:
        return None
    return ("bsi.bund.de", "ai-c4" if m.group(1) == "4" else "c5", None, m.group(2))


def iso_target(line):
    """ISO targets, with the edition resolved or the reference rejected.

    The edition is part of the identifier — secid:control/iso.org/27001@2022#A.5.1 —
    so a clause whose edition cannot be established cannot be minted at all.

    42001 has one edition, 2023, which the column title also states. For 27001 and
    27002 an explicit edition wins. Otherwise the Annex A structure settles it: the
    2022 edition numbers Annex A controls in two parts under A.5 to A.8, and the 2013
    edition in three parts under A.5 to A.18, so the shape is decisive in a way a
    guess would not be. A three-part Annex A reference is therefore a 2013 citation
    inside a mapping to current standards, which is more likely an error than an
    intent, and is held back rather than minted — see issue 17.

    A main-body clause carries no edition signal, since clauses 4 to 10 are numbered
    alike in both editions. These resolve to 2022 because the 2013 edition was
    withdrawn in October 2022 and an unqualified citation published in 2026 means the
    edition in force. That is the one inference this generator makes, and it is
    recorded here rather than buried.
    """
    m = ISO.match(line)
    if not m:
        return None
    if SECOND_CLAUSE.search(line[m.end(3):]):
        return None
    standard, stated, clause = m.group(1), m.group(2), m.group(3)
    if standard == "42001":
        return ("iso.org", "42001", stated or "2023", clause)
    if stated:
        return ("iso.org", standard, stated, clause)
    if clause.startswith(("A.", "B.")) and clause.count(".") > 2:
        return None                      # 2013 Annex A structure; held back
    return ("iso.org", standard, "2022", clause)


COLUMNS = {
    "bsi_ai_c4": {
        "key": "bsi-ai-c4",
        "parse": bsi_target,
        "label": "BSI AIC4 and C5",
        "names": {"ai-c4": "BSI AIC4", "c5": "BSI C5"},
    },
    "iso_iec_42001_2023": {
        "key": "iso",
        "parse": iso_target,
        "label": "ISO/IEC 42001, 27001 and 27002",
        "names": {"42001": "ISO/IEC 42001", "27001": "ISO/IEC 27001",
                  "27002": "ISO/IEC 27002"},
    },
}


def citation(spec, names):
    ns, framework, version, identifier = spec
    stem = names.get(framework, framework)
    return f"{stem}:{version} {identifier}" if version else f"{stem} {identifier}"


def target_path(root, spec):
    ns, framework, version, identifier = spec
    parts = [ns, framework] + ([version] if version else []) + [f"{identifier}.json"]
    return root.joinpath(*parts)


def build_target(spec, names, now):
    ns, framework, version, identifier = spec
    obj = {
        "type": "x-control",
        "spec_version": "2.1",
        "id": f"x-control--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {CONTROL_EXT: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        # A citation the catalog constructs, not the publisher's title. For iso.org
        # the schemas reject anything more than this.
        "name": citation(spec, names),
        "framework_namespace": ns,
        "framework": framework,
        "control_identifier": identifier,
        "status": "live",
        "external_references": [{
            "source_name": "secid",
            "external_id": (f"secid:control/{ns}/{framework}"
                            f"{'@' + version if version else ''}#{identifier}"),
        }],
    }
    if version:
        obj["framework_version"] = version
    return order(obj, CONTROL_KEYS)


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
    return order(obj, MAPPING_KEYS)


def committed_controls(objects, version):
    root = pathlib.Path(objects) / "x-control" / NAMESPACE / "aicm" / version
    if not root.is_dir():
        sys.exit(f"no committed aicm {version} controls at {root}; generate them first")
    out = {}
    for path in sorted(root.glob("*.json")):
        obj = json.loads(path.read_text())
        out[obj["control_identifier"]] = obj["id"]
    return out


def self_test():
    cases = [
        # BSI: only an explicitly prefixed code resolves.
        ("C4 SR-06", ("bsi.bund.de", "ai-c4", None, "SR-06")),
        ("C5 AM-05", ("bsi.bund.de", "c5", None, "AM-05")),
        ("CRY-04", None),                    # unprefixed: 288 of 692 lines
        ("BC-01", None),                     # appears as both C4 and C5 elsewhere
        ("C4 PF-4", None),                   # one digit where the rest use two
        ("C5  SP-02", None),                 # double space
        ("C4 BC-01 (4th bullet)", None),
        ("C4 Section 4 (4.4.2.1)", None),
        ("OIS-01 Additional Criteria", None),
        # ISO: the edition has to be resolvable, because it is part of the identifier.
        ("42001: A.6.2.6", ("iso.org", "42001", "2023", "A.6.2.6")),
        ("42001: A.2.3 Alignment with other organizational policies",
         ("iso.org", "42001", "2023", "A.2.3")),          # title discarded
        ("ISO 27001:2022  A.8.24", ("iso.org", "27001", "2022", "A.8.24")),
        ("27001: A.5.1 Policies for information security",
         ("iso.org", "27001", "2022", "A.5.1")),          # 2-part Annex A: 2022 only
        ("27002: 8.24", ("iso.org", "27002", "2022", "8.24")),
        ("27001: 9.3 Management Review", ("iso.org", "27001", "2022", "9.3")),
        ("27001: A.16.1.2", None),           # 3-part Annex A: 2013 structure, issue 17
        ("A.12.7.1", None),                  # no standard named at all
        ("Measurement", None),               # a title fragment from a wrapped line
        ("8.8 Management of technical vulnerabilities (27001)", None),
        ("42001: A.2.2 - AI Policy and A.6.2.1 - AI System Requirements", None),
        ("42001: A.6.2.4 / B.6.2.4 - AI system verification and validation", None),
    ]
    bad = 0
    for line, want in cases:
        got = bsi_target(line) or iso_target(line)
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {line!r} -> {got}")
        if not ok:
            print(f"       expected {want}")
    for line in ["No Mapping", "No mapping", "Not Applicable",
                 "No Mapping for ISO 42001", "No ISO 42001 mapping."]:
        ok = bool(SENTINEL.match(line))
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} sentinel {line!r}")
    names = COLUMNS["iso_iec_42001_2023"]["names"]
    checks = [
        (citation(("iso.org", "27001", "2022", "A.5.1"), names),
         "ISO/IEC 27001:2022 A.5.1"),
        (citation(("bsi.bund.de", "ai-c4", None, "SR-06"),
                  COLUMNS["bsi_ai_c4"]["names"]), "BSI AIC4 SR-06"),
    ]
    for got, want in checks:
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} citation -> {got!r}")
    total = len(cases) + 5 + len(checks)
    print(f"\n{total - bad}/{total} generator self-tests passed")
    return 1 if bad else 0


def run_column(column, spec, data, controls, args, now, published, version):
    parse, names = spec["parse"], spec["names"]
    clean, held, targets, duplicated = [], [], set(), []
    for control in data["controls"]:
        cell = control["scope_applicability_mappings"][column]
        lines = [l.strip() for l in (cell["control_mapping"] or "").split("\n")
                 if l.strip()]
        real = [l for l in lines if not SENTINEL.match(l)]
        if not real:
            continue
        parsed = {l: parse(l) for l in real}
        if all(parsed.values()):
            # The same clause can be cited twice in one cell under different
            # titles — the source gives 104 clauses more than one title, so
            # "9.2.1 General" and "9.2.1 General - Internal audit" are two strings
            # for one provision. Once titles are discarded they are the same
            # target, and a set of targets holds it once. This is not an edit to
            # the publisher's data: both spellings name the same clause.
            specs, seen = [], set()
            for line in real:
                target = parsed[line]
                if target not in seen:
                    seen.add(target)
                    specs.append(target)
            if len(specs) != len(real):
                duplicated.append(control["control_id"])
            clean.append((control["control_id"], cell, specs))
            targets.update(specs)
        else:
            held.append({
                "control": control["control_id"],
                "gap_level": cell["gap_level"],
                "unparsed": [l for l in real if not parsed[l]],
                "parsed": [l for l in real if parsed[l]],
            })

    out = pathlib.Path(args.out)
    t_tally = emit((target_path(out / "x-control", s), build_target(s, names, now))
                   for s in sorted(targets))
    report(f"{spec['label']} targets", out / "x-control", t_tally)

    ids = {s: json.loads(target_path(out / "x-control", s).read_text())["id"]
           for s in sorted(targets)}
    map_root = (out / "x-gap-mapping" / NAMESPACE / "aicm" / version / spec["key"])
    m_tally = emit((map_root / f"{cid}.json",
                    build_mapping(controls[cid], [ids[s] for s in specs],
                                  cell["gap_level"], cell["addendum"],
                                  published, now))
                   for cid, cell, specs in clean)
    report(f"aicm {version} -> {spec['key']} mappings", map_root, m_tally)

    qpath = pathlib.Path(args.quarantine) / f"aicm-{version}-{spec['key']}.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(json.dumps({
        "source": f"AICM {version}, scope_applicability_mappings.{column}",
        "mappings": str(map_root),
        "why": "These references cannot be resolved to a specific control in a "
               "specific standard, so they are held back rather than guessed at. "
               "Quarantine is per control: a gap verdict is assessed against the "
               "whole set of targets, so publishing it over a subset would assert "
               "something the publisher never assessed.",
        "controls_mapped": len(clean),
        "controls_held": len(held),
        "references_unparsed": sum(len(h["unparsed"]) for h in held),
        "entries": sorted(held, key=lambda h: h["control"]),
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"  quarantine -> {qpath}: {len(clean)} mapped, {len(held)} held")
    if duplicated:
        print(f"  {len(duplicated)} mapped controls cited the same clause more than "
              f"once; the duplicates collapse into one target")
    print()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?")
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
    for column, spec in COLUMNS.items():
        run_column(column, spec, data, controls, args, now, published, version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
