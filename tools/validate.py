#!/usr/bin/env python3
"""Validate CSA-CC objects against the JSON Schemas in schemas/.

Checks the catalog's own custom types. It is not a STIX conformance checker — for
that, run the OASIS validator alongside it:

    stix2_validator --schemas ./schemas/ --enforce-refs bundle.json

Usage:
    tools/validate.py bundle.json [more.json ...]   validate objects in files
    tools/validate.py --self-test                   check the schemas themselves

Accepts a STIX bundle, a bare object, or a list of objects. Objects whose `type`
has no schema here (relationship, identity, extension-definition) are skipped:
they are standard STIX and the OASIS validator owns them.
"""
import glob
import json
import os
import sys
import uuid

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("needs jsonschema: pip install jsonschema")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT, "schemas")


def load_schemas():
    out = {}
    for path in sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.json"))):
        schema = json.load(open(path))
        Draft202012Validator.check_schema(schema)
        out[schema["title"]] = schema
    if not out:
        sys.exit(f"no schemas found in {SCHEMA_DIR}")
    return out


def objects_in(doc):
    """Yield STIX objects from a bundle, a list, or a single object."""
    if isinstance(doc, list):
        for item in doc:
            yield from objects_in(item)
    elif isinstance(doc, dict):
        if doc.get("type") == "bundle" and "objects" in doc:
            yield from objects_in(doc["objects"])
        elif "type" in doc:
            yield doc


def schema_key(obj):
    """Which schema applies to this object.

    Custom SDOs are keyed by `type`. A `relationship` is a standard STIX type, so it
    is keyed by `relationship_type` instead: the catalog defines properties on some
    relationships (csa-gap-mapping) and not others (a plain `mitigates` edge is
    standard and owned by the OASIS validator).
    """
    stix_type = obj.get("type")
    if stix_type == "relationship":
        return obj.get("relationship_type")
    return stix_type


def validate_objects(objs, schemas, label):
    checked = skipped = 0
    failures = []
    for obj in objs:
        key = schema_key(obj)
        schema = schemas.get(key)
        if schema is None:
            skipped += 1
            continue
        checked += 1
        for err in sorted(Draft202012Validator(schema).iter_errors(obj),
                          key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in err.path) or "(object)"
            failures.append(f"{label}: {key} {obj.get('id', '?')}\n"
                            f"    {where}: {err.message}")
    return checked, skipped, failures


def mapping_extension_id(schemas):
    """The extension-definition id the mapping schema requires, read from the schema.

    Taken from the schema rather than hardcoded here, so the self-test cannot pass
    against an id the schema does not actually accept.
    """
    required = schemas["csa-gap-mapping"]["properties"]["extensions"]["required"]
    return required[0]


def self_test(schemas):
    """Confirm the schemas accept valid objects and reject known-bad ones."""
    MAPPING_EXT = mapping_extension_id(schemas)

    def base(t):
        if t == "csa-gap-mapping":
            return {
                "type": "relationship",
                "spec_version": "2.1",
                "id": f"relationship--{uuid.uuid4()}",
                "created": "2026-01-15T00:00:00.000Z",
                "modified": "2026-01-15T00:00:00.000Z",
                "relationship_type": "csa-gap-mapping",
                "source_ref": f"x-control--{uuid.uuid4()}",
                "target_ref": f"x-control--{uuid.uuid4()}",
                "extensions": {
                    MAPPING_EXT: {"extension_type": "toplevel-property-extension"}
                },
                "gap_level": "No Gap",
            }
        return {
            "type": t,
            "spec_version": "2.1",
            "id": f"{t}--{uuid.uuid4()}",
            "created": "2026-01-15T00:00:00.000Z",
            "modified": "2026-01-15T00:00:00.000Z",
            "extensions": {
                f"extension-definition--{uuid.uuid4()}": {"extension_type": "new-sdo"}
            },
        }

    def with_refs(o):
        o.update(assessed_control_ref=f"x-control--{uuid.uuid4()}",
                 entity_ref=f"identity--{uuid.uuid4()}")
        return o

    cases = [
        # (label, type, mutation, should_be_rejected)
        ("status value that was removed", "x-control",
         lambda o: o.update(status="replaced"), True),
        ("spec_version 2.0", "x-control",
         lambda o: o.update(spec_version="2.0"), True),
        ("missing extensions block", "x-control",
         lambda o: o.pop("extensions"), True),
        ("extension_type not new-sdo", "x-control",
         lambda o: o.update(extensions={
             f"extension-definition--{uuid.uuid4()}":
                 {"extension_type": "property-extension"}}), True),
        ("extensions keyed by a non-definition id", "x-control",
         lambda o: o.update(extensions={"x-foo--bar": {"extension_type": "new-sdo"}}), True),
        ("id prefix not matching type", "x-control",
         lambda o: o.update(id=f"x-regulation--{uuid.uuid4()}"), True),
        ("framework_namespace not lowercase", "x-control",
         lambda o: o.update(framework_namespace="ISO.org"), True),
        ("UUIDv5 id where the spec requires v4", "x-control",
         lambda o: o.update(id="x-control--1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d"), True),
        ("ISO control carrying specification", "x-control",
         lambda o: o.update(framework_namespace="iso.org", framework="42001",
                            control_identifier="A.6.1.2",
                            specification="Objectives for responsible development..."), True),
        ("ISO control carrying a description", "x-control",
         lambda o: o.update(framework_namespace="iso.org",
                            description="Requires objectives to be defined."), True),
        ("ISO control carrying audit_guidance", "x-control",
         lambda o: o.update(framework_namespace="iso.org",
                            audit_guidance="Check the documented objectives."), True),
        ("implementation carrying config_snippet", "x-control-implementation",
         lambda o: o.update(config_snippet="resource {}"), True),
        ("implementation carrying vendor_namespace", "x-control-implementation",
         lambda o: o.update(vendor_namespace="amazon.com"), True),
        ("assessment missing assessed_control_ref", "x-control-assessment",
         lambda o: o.update(entity_ref=f"identity--{uuid.uuid4()}"), True),
        ("assessment entity_ref pointing at a control", "x-control-assessment",
         lambda o: with_refs(o).update(entity_ref=f"x-control--{uuid.uuid4()}"), True),
        ("assessment_date not a timestamp", "x-control-assessment",
         lambda o: with_refs(o).update(assessment_date="2026-01-15"), True),
        ("minimal valid control", "x-control", lambda o: None, False),
        ("ISO control as pure citation", "x-control",
         lambda o: o.update(name="ISO/IEC 42001:2023 A.6.1.2", framework_namespace="iso.org",
                            framework="42001", framework_version="2023",
                            control_identifier="A.6.1.2"), False),
        ("CSA control carrying its own specification", "x-control",
         lambda o: o.update(framework_namespace="cloudsecurityalliance.org", framework="aicm",
                            specification="Training pipelines are secured..."), False),
        ("capability with audit and remediation guidance", "x-capability",
         lambda o: o.update(vendor_namespace="amazon.com", product="aws/s3",
                            audit_guidance="Check bucket encryption configuration.",
                            remediation_guidance="Apply an SSE-KMS default."), False),
        ("valid regulation", "x-regulation",
         lambda o: o.update(name="Security of processing", regulation="gdpr",
                            regulation_namespace="europa.eu"), False),
        ("valid capability", "x-capability",
         lambda o: o.update(vendor_namespace="amazon.com", product="aws/s3"), False),
        ("valid implementation", "x-control-implementation",
         lambda o: o.update(implementation_type=["configuration"]), False),
        ("valid assessment", "x-control-assessment", with_refs, False),

        # csa-gap-mapping
        ("mapping with an invented gap level", "csa-gap-mapping",
         lambda o: o.update(gap_level="Some Gap"), True),
        ("mapping with a lowercase gap level", "csa-gap-mapping",
         lambda o: o.update(gap_level="no gap"), True),
        ("mapping missing gap_level entirely", "csa-gap-mapping",
         lambda o: o.pop("gap_level"), True),
        ("mapping with the wrong relationship_type", "csa-gap-mapping",
         lambda o: o.update(relationship_type="maps-to"), True),
        ("mapping referencing a foreign extension id", "csa-gap-mapping",
         lambda o: o.update(extensions={
             f"extension-definition--{uuid.uuid4()}":
                 {"extension_type": "toplevel-property-extension"}}), True),
        ("mapping declared as new-sdo rather than a property extension",
         "csa-gap-mapping",
         lambda o: o.update(extensions={
             MAPPING_EXT: {"extension_type": "new-sdo"}}), True),
        ("mapping targeting a capability", "csa-gap-mapping",
         lambda o: o.update(target_ref=f"x-capability--{uuid.uuid4()}"), True),
        ("mapping with a non-boolean bidirectional", "csa-gap-mapping",
         lambda o: o.update(bidirectional="yes"), True),
        ("valid mapping, control to control", "csa-gap-mapping",
         lambda o: o.update(gap_level="Partial Gap",
                            description="Scope differs: the target is narrower."), False),
        ("valid mapping to a regulation clause", "csa-gap-mapping",
         lambda o: o.update(target_ref=f"x-regulation--{uuid.uuid4()}",
                            gap_level="Full Gap"), False),
        ("valid bidirectional mapping", "csa-gap-mapping",
         lambda o: o.update(bidirectional=True), False),
    ]

    bad = 0
    for label, stix_type, mutate, expect_reject in cases:
        obj = base(stix_type)
        mutate(obj)
        rejected = bool(list(Draft202012Validator(schemas[stix_type]).iter_errors(obj)))
        ok = rejected == expect_reject
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {label} "
              f"({'rejected' if rejected else 'accepted'})")
    print(f"\n{len(cases) - bad}/{len(cases)} self-tests passed")
    return 1 if bad else 0


def main(argv):
    schemas = load_schemas()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--self-test":
        print(f"{len(schemas)} schemas loaded: {', '.join(sorted(schemas))}\n")
        return self_test(schemas)

    total_checked = total_skipped = 0
    all_failures = []
    for path in argv:
        try:
            doc = json.load(open(path))
        except (OSError, json.JSONDecodeError) as exc:
            all_failures.append(f"{path}: unreadable — {exc}")
            continue
        checked, skipped, failures = validate_objects(objects_in(doc), schemas, path)
        total_checked += checked
        total_skipped += skipped
        all_failures += failures

    for failure in all_failures:
        print(failure)
    print(f"\n{total_checked} object(s) checked, {total_skipped} skipped "
          f"(standard STIX types), {len(all_failures)} problem(s)")
    return 1 if all_failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
