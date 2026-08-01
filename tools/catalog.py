"""Shared pieces for the catalog's generators.

The minted identifiers live here once. A second copy of an extension-definition
id in a second generator is the kind of thing that drifts silently and then emits
objects no consumer has a definition for, so generators import them rather than
restating them.
"""

import json

CONTROL_EXT = "extension-definition--8905b9e8-0738-435f-8989-83ea731db5ea"
TLP_WHITE = "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"
CSA_IDENTITY = "identity--51f9d480-d80b-4415-93c7-507cde4d1e85"

NAMESPACE = "cloudsecurityalliance.org"


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
