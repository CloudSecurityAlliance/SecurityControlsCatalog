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

CONTROL_EXT = "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea"
TLP_WHITE = "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"
CSA_IDENTITY = "identity--51f9d480-d80b-4415-93c7-507cde4d1e85"

NAMESPACE = "cloudsecurityalliance.org"
FRAMEWORK = "aicm"

# Taxonomy columns the source answers for every control. Omitted when the answer
# is "none" — see prune_empty.
TAXONOMY_PROPERTIES = ("threat_category", "stack_components", "lifecycle_relevance")

# Order the properties as SCHEMA-STIX-OBJECT-EXTENSIONS.md presents them, so a
# generated object and a documented example read the same way in a diff.
KEY_ORDER = [
    "type", "spec_version", "id", "created", "modified", "object_marking_refs",
    "extensions", "created_by_ref", "name", "framework_namespace", "framework",
    "framework_version", "control_identifier", "domain", "status", "valid_from",
    "specification", "control_type", "threat_category",
    "typical_control_applicability_and_ownership", "stack_components",
    "lifecycle_relevance", "implementation_guidelines", "auditing_guidelines",
    "external_references",
]


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
    obj = prune_empty(obj)
    return {k: obj[k] for k in KEY_ORDER if k in obj}


def reconcile(fresh, path):
    """Carry an already-published object's identity onto a regenerated one."""
    if not path.exists():
        return fresh, "new"
    old = json.loads(path.read_text())
    fresh["id"] = old["id"]
    fresh["created"] = old["created"]
    comparable = dict(fresh, modified=old["modified"])
    if comparable == old:
        return old, "unchanged"
    return fresh, "updated"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="the AICM JSON distribution")
    ap.add_argument("--out", default="objects",
                    help="objects directory (default: objects)")
    ap.add_argument("--now", help="timestamp for newly minted objects "
                                  "(default: the current UTC time)")
    args = ap.parse_args(argv)

    now = args.now or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    data = json.loads(pathlib.Path(args.source).read_text())
    version = data["specification_version"]
    published = f"{data['published']}T00:00:00.000Z"

    out = pathlib.Path(args.out) / "x-control" / NAMESPACE / FRAMEWORK / version
    out.mkdir(parents=True, exist_ok=True)

    tally = {"new": 0, "updated": 0, "unchanged": 0}
    for control in data["controls"]:
        path = out / f"{control['control_id']}.json"
        obj, state = reconcile(build(control, version, published, now), path)
        tally[state] += 1
        if state != "unchanged":
            path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

    print(f"{FRAMEWORK} {version} -> {out}")
    print(f"  {tally['new']} new, {tally['updated']} updated, "
          f"{tally['unchanged']} unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
