#!/usr/bin/env python3
"""Generate x-control objects from a published AICM release.

Run against the AICM JSON distribution:

    python3 tools/generate_aicm_controls.py path/to/aicm-1.1.0.json

Re-running is safe and is the expected way to pick up a corrected source. An
object's id and created timestamp are read back from the committed file and
preserved, and modified is bumped only when something else actually changed, so
a no-op run writes nothing. STIX requires a UUIDv4 for SDO identifiers, which by
construction cannot be derived from content: re-minting on every run would break
every reference a consumer holds. See objects/README.md.

Mappings and CAIQ questions are present in the same source but are not emitted
here. They are separate object types with their own open data questions, and
generating them belongs in their own change.
"""

import argparse
import datetime
import json
import pathlib
import sys
import uuid

from catalog import (CONTROL_EXT, CSA_IDENTITY, KEY_ORDER, NAMESPACE, TLP_WHITE,
                     emit, order, report)

FRAMEWORK = "aicm"

# Taxonomy columns the source answers for every control. Omitted when the answer
# is "none" — see prune_empty.
TAXONOMY_PROPERTIES = ("threat_category", "stack_components", "lifecycle_relevance")


def flags_to_list(mapping):
    """Boolean columns become the values that are true."""
    return [k for k, v in mapping.items() if v]


def drop_blanks(mapping):
    """Text columns become only the entries the source filled in.

    A blank means the row does not apply — a lifecycle phase the control has no
    bearing on, or a layer with no stated owner — so the key is dropped rather
    than carried as null.
    """
    return {k: v for k, v in mapping.items() if v is not None and str(v).strip()}


def prune_empty(obj):
    """Drop taxonomy properties that came out empty.

    The source answers every taxonomy column for every control, so "none of them"
    is an answer the publisher gave: 15 Human Resources controls apply to no stack
    layer, BCR-11 and GRC-08 to no threat category, UEM-06 to no lifecycle phase.
    STIX cannot carry that answer. Empty lists and empty dictionaries are
    prohibited, which makes an empty value and an absent property the same thing
    on the wire, so the distinction between "assessed, and none applied" and "the
    source never said" is not expressible without either departing from STIX or
    inventing a sentinel. Both were rejected; the property is omitted instead.

    Within one framework version the answer is still recoverable, because the
    source assesses every control against every column and these objects are
    generated from it — but it is recoverable from the framework rather than from
    the object, and that limit is worth stating plainly.
    """
    return {k: v for k, v in obj.items()
            if k not in TAXONOMY_PROPERTIES or v}


def build(control, version, published, now):
    cid = control["control_id"]
    obj = {
        "type": "x-control",
        "spec_version": "2.1",
        "id": f"x-control--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {CONTROL_EXT: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        "name": control["control_title"],
        "framework_namespace": NAMESPACE,
        "framework": FRAMEWORK,
        "framework_version": version,
        "control_identifier": cid,
        "domain": control["control_domain"],
        "status": "live",
        "valid_from": published,
        "specification": control["control_specification"],
        "control_type": control["control_type"],
        "threat_category": flags_to_list(control["threat_category"]),
        "typical_control_applicability_and_ownership": drop_blanks(
            control["typical_control_applicability_and_ownership"]),
        "stack_components": flags_to_list(
            control["architectural_relevance_ai_stack_components"]),
        "lifecycle_relevance": drop_blanks(control["lifecycle_relevance"]),
        "implementation_guidelines": drop_blanks(control["implementation_guidelines"]),
        "auditing_guidelines": drop_blanks(control["auditing_guidelines"]),
        "external_references": [{
            "source_name": "secid",
            "external_id": f"secid:control/{NAMESPACE}/{FRAMEWORK}@{version}#{cid}",
        }],
    }
    # The schema requires at least one entry in these, and the source always has
    # one. Fail loudly rather than emit a control with no guidance at all.
    for prop in ("typical_control_applicability_and_ownership",
                 "implementation_guidelines", "auditing_guidelines"):
        if not obj[prop]:
            sys.exit(f"{cid}: {prop} is empty in the source; refusing to emit")
    return order(prune_empty(obj), KEY_ORDER["x-control"])


def self_test():
    """Confirm the generator carries a publisher's text through untouched.

    Published control text is not clean — AICM 1.1.0 carries spreadsheet artefacts
    throughout — and tidying it in transit would change what the catalog asserts a
    publisher requires. The edit that looks safest is the one most likely to matter:
    a double space separating two clauses, a line break inside a list. See
    CONVENTIONS-STIX-MODELING.md section 10.
    """
    messy = ("Establish, document, approve  and maintain policies.\r\n"
            "\t1. Review annually.\n\n2. Retain “records” for 3–5 years. ")
    control = {
        "control_id": "TST-01",
        "control_title": "  Padded   Title  ",
        "control_domain": "Audit & Assurance",
        "control_specification": messy,
        "control_type": "Cloud & AI Related",
        "typical_control_applicability_and_ownership": {"model": messy},
        "architectural_relevance_ai_stack_components": {"compute": True},
        "lifecycle_relevance": {"development": messy, "delivery": None},
        "threat_category": {"model_theft": True},
        "implementation_guidelines": {"shared": messy},
        "auditing_guidelines": {"ai_customer": messy},
    }
    obj = build(control, "1.1.0", "2026-06-22T00:00:00.000Z",
                "2026-01-15T00:00:00.000Z")
    checks = [
        ("name", obj["name"], control["control_title"]),
        ("specification", obj["specification"], messy),
        ("domain", obj["domain"], control["control_domain"]),
        ("implementation_guidelines", obj["implementation_guidelines"]["shared"], messy),
        ("auditing_guidelines", obj["auditing_guidelines"]["ai_customer"], messy),
        ("lifecycle_relevance", obj["lifecycle_relevance"]["development"], messy),
        ("applicability", obj["typical_control_applicability_and_ownership"]["model"], messy),
    ]
    bad = 0
    for label, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {label} carried verbatim")
        if not ok:
            print(f"       published {want!r}\n       carried   {got!r}")

    # A blank cell means the row does not apply and is dropped; a cell holding only
    # whitespace is blank. Neither is a licence to edit a cell that has content.
    ok = "delivery" not in obj["lifecycle_relevance"]
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} blank lifecycle phase dropped rather than carried as null")

    # Round-tripping through the file format must not touch the text either.
    ok = json.loads(json.dumps(obj, ensure_ascii=False))["specification"] == messy
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} text survives the JSON round-trip")

    total = len(checks) + 2
    print(f"\n{total - bad}/{total} generator self-tests passed")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", help="the AICM JSON distribution")
    ap.add_argument("--self-test", action="store_true",
                    help="check that a publisher's text is carried untouched")
    ap.add_argument("--out", default="objects",
                    help="objects directory (default: objects)")
    ap.add_argument("--now", help="timestamp for newly minted objects "
                                  "(default: the current UTC time)")
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

    out = pathlib.Path(args.out) / "x-control" / NAMESPACE / FRAMEWORK / version
    tally = emit((out / f"{c['control_id']}.json",
                  build(c, version, published, now)) for c in data["controls"])
    report(f"{FRAMEWORK} {version}", out, tally)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
