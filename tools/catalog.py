"""Shared pieces for the catalog's generators.

The minted identifiers live here once. A second copy of an extension-definition
id in a second generator is the kind of thing that drifts silently and then emits
objects no consumer has a definition for, so generators import them rather than
restating them.

The same argument applies to property order. Every writer of a given type — the
generators, and the YAML view's write-back path — has to agree on it or the same
object acquires a different byte layout depending on which tool touched it last,
and every such difference shows up as a spurious diff. So KEY_ORDER is the single
home for that too.
"""

import json
import pathlib

CONTROL_EXT = "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea"
REGULATION_EXT = "extension-definition--a72496a3-08f8-43fb-88c9-479bb94e5e02"
MAPPING_EXT = "extension-definition--b1d89841-2dc0-4559-af18-380ecd4c1682"
TLP_WHITE = "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"
CSA_IDENTITY = "identity--51f9d480-d80b-4415-93c7-507cde4d1e85"

NAMESPACE = "cloudsecurityalliance.org"

# Which extension definition each custom type declares itself through. A custom
# type is identified by the definition its instances reference, not by the `type`
# string, so this mapping is what lets a tool reconstruct the `extensions`
# property from the type alone — see CONVENTIONS-STIX-MODELING.md section 5.
EXTENSION_FOR_TYPE = {
    "x-control": CONTROL_EXT,
    "x-regulation": REGULATION_EXT,
    "x-gap-mapping": MAPPING_EXT,
}

# Property order per type, as SCHEMA-STIX-OBJECT-EXTENSIONS.md presents them, so a
# generated object and a documented example read the same way in a diff.
#
# One order per type covers every writer, because the objects that carry fewer
# properties carry a *subsequence* of the same order: a citation-only control and
# a CAIQ question are both x-control with some properties absent, not with the
# survivors rearranged. order() drops what is missing and keeps the rest in place,
# so a narrower writer needs no narrower list.
KEY_ORDER = {
    "x-control": [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "extensions", "created_by_ref", "name", "framework_namespace", "framework",
        "framework_version", "control_identifier", "domain", "status", "valid_from",
        "specification", "control_type", "threat_category",
        "typical_control_applicability_and_ownership", "stack_components",
        "lifecycle_relevance", "implementation_guidelines", "auditing_guidelines",
        "external_references",
    ],
    "x-regulation": [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "extensions", "created_by_ref", "name", "regulation_namespace",
        "regulation", "clause_identifier", "publication_id", "jurisdiction",
        "external_references",
    ],
    "x-gap-mapping": [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "extensions", "created_by_ref", "source_ref", "target_refs", "gap_level",
        "description", "valid_from",
    ],
    "relationship": [
        "type", "spec_version", "id", "created", "modified", "object_marking_refs",
        "created_by_ref", "relationship_type", "source_ref", "target_ref",
    ],
}


# Which generator produces each committed object, keyed by the provenance a caller
# can read off the object and its path.
#
# This exists because every object under objects/ is generated, without exception.
# Nothing here is hand-authored content, so an edit made directly to a committed
# object — including one made through the YAML view — is overwritten the next time
# its generator runs. reconcile() preserves `id` and `created` and takes everything
# else from the generator, by design.
#
# A tool that writes to a committed object therefore owes the caller the name of the
# generator that will overwrite it, and the remedy. Keyed coarsely on purpose: the
# useful answer is "which generator, and is the fix upstream or in the conversion",
# not a per-property provenance table that would drift against the generators.
#
# CI requires every committed object to resolve through this map, so adding a
# generator without adding its entry fails rather than silently reporting nothing.
GENERATED_BY = {
    ("x-control", "cloudsecurityalliance.org", "aicm"):
        "tools/generate_aicm_controls.py",
    ("x-control", "cloudsecurityalliance.org", "aicm-caiq"):
        "tools/generate_aicm_caiq.py",
    ("x-control", "iso.org", None): "tools/generate_aicm_standard_mappings.py",
    ("x-control", "bsi.bund.de", None): "tools/generate_aicm_standard_mappings.py",
    ("x-regulation", "europa.eu", None): "tools/generate_aicm_eu_mappings.py",
    ("x-gap-mapping", None, "ai-act"): "tools/generate_aicm_eu_mappings.py",
    ("x-gap-mapping", None, "iso"): "tools/generate_aicm_standard_mappings.py",
    ("x-gap-mapping", None, "bsi-ai-c4"): "tools/generate_aicm_standard_mappings.py",
}


def provenance_key(obj, path):
    """The (type, namespace, name) a GENERATED_BY lookup is keyed on.

    A control and a regulation carry their provenance as properties. A gap mapping
    does not — its own identity is the claim, not a framework — so its target comes
    from the committed path, which CI already requires to agree with the object.
    """
    stix_type = obj.get("type")
    if stix_type == "x-control":
        return (stix_type, obj.get("framework_namespace"), obj.get("framework"))
    if stix_type == "x-regulation":
        return (stix_type, obj.get("regulation_namespace"), obj.get("regulation"))
    if stix_type == "x-gap-mapping":
        parts = pathlib.PurePath(path).parts
        # objects/x-gap-mapping/<namespace>/<framework>/<version>/<target>/<id>.json
        return (stix_type, None, parts[5] if len(parts) > 6 else None)
    return (stix_type, None, None)


def generated_by(obj, path):
    """The generator that will overwrite this object, or None if it is not known.

    Falls back to a namespace-wide entry, so a new ISO edition or BSI standard is
    covered without touching the map.
    """
    stix_type, namespace, name = provenance_key(obj, path)
    for key in ((stix_type, namespace, name), (stix_type, namespace, None),
                (stix_type, None, name)):
        if key in GENERATED_BY:
            return GENERATED_BY[key]
    return None


def order(obj, key_order):
    """Put properties in a fixed order so a diff reads the same way every time."""
    known = [k for k in key_order if k in obj]
    rest = sorted(k for k in obj if k not in key_order)
    if rest:
        raise SystemExit(f"unordered properties would be emitted last: {rest}")
    return {k: obj[k] for k in known}


def reconcile(fresh, path):
    """Carry an already-published object's identity onto a regenerated one.

    STIX requires a UUIDv4 for SDO identifiers, which by construction cannot be
    derived from content. A generator that re-mints on every run would break every
    reference a consumer holds, so the committed id and created timestamp win and
    modified moves only when something else actually changed.
    """
    if not path.exists():
        return fresh, "new"
    old = json.loads(path.read_text())
    fresh["id"] = old["id"]
    fresh["created"] = old["created"]
    if dict(fresh, modified=old["modified"]) == old:
        return old, "unchanged"
    return fresh, "updated"


def emit(pairs):
    """Write (path, object) pairs, preserving identity, and report what moved."""
    tally = {"new": 0, "updated": 0, "unchanged": 0}
    for path, fresh in pairs:
        path.parent.mkdir(parents=True, exist_ok=True)
        obj, state = reconcile(fresh, path)
        tally[state] += 1
        if state != "unchanged":
            path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    return tally


def report(label, out, tally):
    print(f"{label} -> {out}")
    print(f"  {tally['new']} new, {tally['updated']} updated, "
          f"{tally['unchanged']} unchanged")
