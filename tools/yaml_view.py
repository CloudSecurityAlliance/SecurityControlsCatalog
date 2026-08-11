#!/usr/bin/env python3
"""A YAML view of committed objects, for reading and correcting them.

    python3 tools/yaml_view.py objects/x-control/.../MDS-01.json   # show the view
    python3 tools/yaml_view.py --write view.yaml                   # write it back
    python3 tools/yaml_view.py --check                             # round-trip every object

The catalog's committed form is STIX 2.1 JSON, and that is what consumers get. It
is not, however, what a person should have to read to check a control's guidance
text or correct a domain name. This produces a YAML rendering of one object with
the machinery removed, and takes an edited rendering back to the exact JSON.

## What the view leaves out, and why that is the point

Seven properties never appear in the view:

    spec_version  id  created  modified  object_marking_refs  extensions  created_by_ref

Each is either a constant for every object in the catalog (`spec_version`, the
TLP marking, the CSA identity, the extension body) or minted and then permanent
(`id`, `created`, `modified`). None was ever meant to be authored by hand —
`catalog.reconcile` exists precisely so that regenerating an object does not
disturb them. So the UUIDs and timestamps that make the JSON unpleasant to read
are not information a reviewer is withholding judgement on; they are bookkeeping,
and the view drops them and restores them mechanically.

What is left is the content: the name, the framework coordinates, the
specification, the guidance, the mapping verdict. That is the part a human has an
opinion about.

## What it does not do

It does not author new objects. `--write` requires an already-committed file to
write back to, because an object's `id` is minted once and must not be re-minted
(CONVENTIONS-STIX-MODELING.md section 3), and because catalog content comes from
published source releases through the generators in this directory rather than
from a hand-written file. The view is for reviewing and correcting what is
already here — which is what a contributor actually does — not for adding a
control by hand.

It also refuses a property the type's schema does not define. A new property is a
schema change and belongs in a schema change, not in an edited view.

## What --write checks before it writes anything

The point of the view is that a person edits it, so the edit is exactly where a bad
value enters. Nothing is written until all of these pass:

- the file parses as YAML — reported with line and column, because indentation is
  significant and a whitespace slip is a syntax error rather than a cosmetic one;
- no value was resolved to a non-string by YAML's scalar rules. This is the trap the
  format brings with it: `no`, `on`, `null`, `~`, a bare version number, an unquoted
  timestamp are each plain text to the person typing and a bool, None, float, or date
  to the loader. Reported in the terms that fix it (quote it), because *"True is not
  of type 'string'"* does not help someone who typed `no`;
- the view's `type` matches the object committed at that path;
- no property that decides the object's path or SecID has changed — editing one names
  a *different* object, which a generator mints with its own identifier rather than a
  view producing by renaming this one;
- the rebuilt object satisfies its JSON Schema, checked with the same code path as
  `tools/validate.py`.

Afterwards it prints which properties were added, changed, or removed. A removal is
legal — the schemas require few properties — but it is the edit most easily made by
accident, and an unreported one looks identical to no edit at all.

## An edit here is not durable, and a write says so

**Nothing under `objects/` is hand-authored.** Every committed object is produced by a
generator in this directory, and `catalog.reconcile` preserves only `id` and `created`
while taking all content from the generator. So an edit written back through this tool
is overwritten the next time its generator runs — silently, and looking exactly like no
edit at all.

That makes the view a **second writer** with no precedence over the first, which is a
real source-of-truth problem rather than a cosmetic one: a contributor who corrects a
typo and watches it vanish a release later has been misled by this tool, which is worse
than not having it.

So every write names the generator that will overwrite it and both remedies — the fix
is upstream if the publisher's data is wrong (the catalog does not tidy a publisher's
data in transit, see CONVENTIONS-STIX-MODELING.md section 10), and in the generator if
the conversion is wrong. Editing here stays useful for seeing the corrected object and
for checking what a generator change should produce; it is not a way to hold a
correction.

## Why --check is the load-bearing part

A view that loses anything is worse than no view, and the risk is not
hypothetical: published control text carries carriage returns, tabs, trailing
spaces, and typographic quotes (see CONVENTIONS-STIX-MODELING.md section 10,
which forbids tidying any of it in transit). YAML block scalars cannot represent
all of that, so the writer below uses a readable block only where it is provably
lossless and falls back to a quoted scalar otherwise.

`--check` is what makes that claim checkable: it renders every committed object,
reads the rendering back, and requires the result to be byte-identical to the file
on disk. It runs in CI.
"""

import argparse
import datetime
import glob
import json
import os
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("needs PyYAML: pip install pyyaml")

from catalog import (CSA_IDENTITY, EXTENSION_FOR_TYPE, KEY_ORDER, TLP_WHITE,
                     generated_by, order, reconcile)
from validate import load_schemas, validate_objects

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"

# The properties the view drops and restores. Verified constant or generator-owned
# across every committed object; --check re-verifies it on every run.
GENERATED = ("spec_version", "id", "created", "modified", "object_marking_refs",
             "extensions", "created_by_ref")

# STIX 2.1 common properties (spec section 3.2). The catalog's schemas describe
# only the properties each custom type adds, so a property from this set is
# legitimate on any object without appearing in a schema's `properties`.
STIX_COMMON = frozenset((
    "type", "spec_version", "id", "created_by_ref", "created", "modified",
    "revoked", "labels", "confidence", "lang", "external_references",
    "object_marking_refs", "granular_markings", "extensions",
))

# Types the view covers: the custom SDOs that hold catalog content. A relationship
# is derived from the objects it links and is emitted by a generator, never edited;
# the identity, marking-definition, and extension-definition objects are machinery
# with one instance each.
VIEWABLE = tuple(EXTENSION_FOR_TYPE)

# The properties that decide an object's path and its SecID. Editing one does not
# correct an object, it names a different one — and that object has to be minted by
# a generator, with its own identifier, rather than produced by renaming this one.
# So a view may change content and must not change these. x-gap-mapping has no such
# tuple: its path derives from the control it is asserted about.
IDENTITY_PROPERTIES = {
    "x-control": ("framework_namespace", "framework", "framework_version",
                  "control_identifier"),
    "x-regulation": ("regulation_namespace", "regulation", "clause_identifier"),
    "x-gap-mapping": ("source_ref",),
}


def schema_properties(stix_type):
    """The property names the type's schema defines, or None if it has no schema."""
    path = SCHEMA_DIR / f"{stix_type}.json"
    if not path.exists():
        return None
    return set(json.loads(path.read_text()).get("properties", {}))


def block_safe(text):
    """Whether a literal block scalar can carry this string without altering it.

    A block scalar strips trailing whitespace from every line and normalises line
    endings, so text that relies on either cannot use one. Published control text
    does rely on both, which is why this check exists rather than a blanket
    preference for the prettier style.
    """
    if "\r" in text or "\t" in text:
        return False
    if not text.endswith("\n") and text != text.rstrip():
        return False
    lines = text.split("\n")
    if any(line != line.rstrip() for line in lines):
        return False
    # A first line starting with a space needs an explicit indentation indicator.
    return not any(line.startswith(" ") for line in lines)


class ViewDumper(yaml.SafeDumper):
    """Emits multi-line prose as a readable block where that is lossless."""


def represent_str(dumper, data):
    if "\n" in data and block_safe(data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


ViewDumper.add_representer(str, represent_str)


def project(obj):
    """The object with its generated properties removed."""
    if obj.get("type") not in VIEWABLE:
        raise SystemExit(
            f"{obj.get('type')} has no view: the view covers {', '.join(VIEWABLE)}. "
            "Relationships and the extension/identity/marking objects are generated.")
    return {k: v for k, v in obj.items() if k not in GENERATED}


def to_yaml(obj, source=None):
    """Render one object as YAML, with a header saying where it came from."""
    header = ""
    if source:
        rel = os.path.relpath(source, ROOT)
        header = (f"# View of {rel}\n"
                  f"# Edit and write back with: python3 tools/yaml_view.py --write <file>\n"
                  f"# Generated properties (id, timestamps, markings, extension) are\n"
                  f"# restored from the committed object and are not editable here.\n"
                  f"source: {rel}\n")
    body = yaml.dump(project(obj), Dumper=ViewDumper, sort_keys=False,
                     allow_unicode=True, default_flow_style=False, width=100)
    return header + body


def resolve_target(source):
    """The committed object a view writes to, refusing anything outside objects/.

    `source` names the file this view writes to, and it arrives inside the file
    rather than on the command line. An absolute path replaces ROOT outright and a
    `..` walks out of it, so an unchecked value could name any writable path on the
    machine. A view may only correct a committed object.
    """
    objects_dir = (ROOT / "objects").resolve()
    target = (ROOT / source).resolve()
    if not target.is_relative_to(objects_dir):
        raise SystemExit(f"source must name a file under objects/, not {source!r}")
    return target


def coercions(view):
    """Values YAML resolved to something other than a string.

    This is the failure the format invites. `no`, `yes`, `on`, `off`, `null`, `~`, a
    leading-zero number, a bare version, an unquoted timestamp — each is a plain
    string to the person typing it and a bool, None, int, float, or date to the
    loader. The schema does reject most of them, but "True is not of type 'string'"
    does not tell someone who typed `no` what to do, so they are reported here in
    the terms that fix them.
    """
    found = []
    for key, value in sorted(view.items()):
        if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
            found.append(f"{key}: {value!r} — YAML read this as "
                         f"{type(value).__name__}; quote it to keep it text")
        elif isinstance(value, datetime.date):
            found.append(f"{key}: {value!r} — YAML read this as a date; "
                         "quote it to keep the published timestamp exactly")
    return found


def restore(view, committed, now, schemas=None):
    """Rebuild the full STIX object from a view plus the committed object it edits.

    The generated properties come back from three places: constants for the whole
    catalog, the type for the extension, and the committed file for the identity
    and timestamps. Nothing about them is inferred from the view.

    Pass `schemas` to validate the result before it is returned. --write always
    does; the round-trip check does not, because it compares against a committed
    object that CI validates separately.
    """
    stix_type = view.get("type")
    if stix_type not in VIEWABLE:
        raise SystemExit(f"view has type {stix_type!r}; expected one of {', '.join(VIEWABLE)}")
    if committed.get("type") != stix_type:
        raise SystemExit(
            f"the view says type {stix_type!r} but {committed.get('type')!r} is "
            f"committed at that path. A view corrects one object; it cannot turn it "
            f"into another type — that object is minted by a generator.")

    changed = [p for p in IDENTITY_PROPERTIES.get(stix_type, ())
               if view.get(p) != committed.get(p)]
    if changed:
        raise SystemExit(
            f"{stix_type}: the view changes {changed}, which decide this object's path "
            f"and SecID. Changing one names a different object, and that object is "
            f"minted by a generator with its own identifier rather than by renaming "
            f"this one.")

    wrong_type = coercions(view)
    if wrong_type:
        raise SystemExit("YAML resolved these to non-text values:\n  "
                         + "\n  ".join(wrong_type))

    defined = schema_properties(stix_type)
    if defined is not None:
        unknown = sorted(k for k in view
                         if k != "source" and k not in defined and k not in STIX_COMMON)
        if unknown:
            raise SystemExit(
                f"{stix_type}: schemas/{stix_type}.json does not define {unknown}. "
                "Adding a property is a schema change, not a view edit.")

    obj = dict(view)
    obj.pop("source", None)
    obj.update({
        "type": stix_type,
        "spec_version": "2.1",
        "id": committed["id"],
        "created": committed["created"],
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {EXTENSION_FOR_TYPE[stix_type]: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
    })
    obj = order(obj, KEY_ORDER[stix_type])

    if schemas is not None:
        _, _, failures = validate_objects([obj], schemas, "edited view")
        if failures:
            raise SystemExit("the edited view does not satisfy "
                             f"schemas/{stix_type}.json:\n" + "\n".join(failures))
    return obj


def check(paths):
    """Round-trip every object and require the result to be byte-identical.

    Reports the split between readable block scalars and quoted fallbacks too,
    since a view that is correct but unreadable has not done its job either.
    """
    checked = skipped = blocks = 0
    failures = []
    for path in paths:
        text = path.read_text()
        obj = json.loads(text)
        if obj.get("type") not in VIEWABLE:
            skipped += 1
            continue
        rendered = to_yaml(obj)
        back = restore(yaml.safe_load(rendered), obj, obj["modified"])
        got = json.dumps(back, indent=2, ensure_ascii=False) + "\n"
        checked += 1
        blocks += rendered.count(": |\n") + rendered.count(": |-\n")
        if got != text:
            failures.append((path, first_difference(text, got)))
    return checked, skipped, blocks, failures


def first_difference(want, got):
    """Where two renderings diverge, for a message that says something useful."""
    for i, (a, b) in enumerate(zip(want, got)):
        if a != b:
            return f"byte {i}: committed {want[i:i + 40]!r} != round-tripped {got[i:i + 40]!r}"
    if len(want) != len(got):
        return f"length {len(want)} != {len(got)}"
    return "identical"


def self_test():
    """Check the view against the cases that would make it unsafe to trust.

    The corpus check (--check) proves the round trip on what is committed today.
    These cases cover what a future object could contain and what an editor could
    do wrong, neither of which the corpus exercises.
    """
    results = []

    def ok(label, condition):
        results.append((label, bool(condition)))

    # Published text carries carriage returns, tabs, trailing spaces and
    # typographic quotes, and section 10 forbids tidying any of it. The block
    # scalar cannot hold most of that, so the writer has to decline it.
    messy = ("Establish, document, approve  and maintain policies.\r\n"
             "\t1. Review annually.\n\n2. Retain “records” for 3–5 years. ")
    ok("carriage returns are not offered to a block scalar", not block_safe(messy))
    ok("trailing whitespace is not offered to a block scalar",
       not block_safe("two lines\nwith trailing space \n"))
    ok("clean multi-line prose is offered to a block scalar",
       block_safe("first paragraph\n\nsecond paragraph\n"))
    ok("a leading space is not offered to a block scalar", not block_safe(" indented\nlines\n"))

    control = {
        "type": "x-control", "spec_version": "2.1",
        "id": "x-control--00000000-0000-4000-8000-000000000000",
        "created": "2026-01-15T00:00:00.000Z", "modified": "2026-01-15T00:00:00.000Z",
        "object_marking_refs": [TLP_WHITE],
        "extensions": {EXTENSION_FOR_TYPE["x-control"]: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        "name": "Test", "framework_namespace": "cloudsecurityalliance.org",
        "framework": "aicm", "framework_version": "1.1.0",
        "control_identifier": "TST-01", "domain": "Audit & Assurance",
        "status": "live", "specification": messy,
        "implementation_guidelines": {"shared": messy},
        "external_references": [{"source_name": "secid", "external_id": "secid:x"}],
    }
    control = order(control, KEY_ORDER["x-control"])
    back = restore(yaml.safe_load(to_yaml(control)), control, control["modified"])
    ok("an object carrying messy published text round-trips exactly", back == control)
    ok("the messy text itself is unaltered", back["specification"] == messy)

    # The view must not become a second way to mint or move an identifier.
    view = yaml.safe_load(to_yaml(control))
    ok("the view withholds the generated properties",
       not any(k in view for k in GENERATED if k != "type"))
    edited = dict(view, domain="Cryptography, Encryption & Key Management")
    rebuilt = restore(edited, control, "2026-08-11T00:00:00.000Z")
    ok("an edit keeps the committed id", rebuilt["id"] == control["id"])
    ok("an edit keeps the committed created", rebuilt["created"] == control["created"])
    ok("an edit moves modified", rebuilt["modified"] == "2026-08-11T00:00:00.000Z")
    ok("an edit changes only the edited property",
       {k for k in rebuilt if rebuilt[k] != control.get(k)} == {"domain", "modified"})

    # Refusals. Each of these would otherwise let a view do something a view
    # should not be able to do.
    def refuses(fn):
        try:
            fn()
        except SystemExit:
            return True
        return False

    ok("a property no schema defines is refused",
       refuses(lambda: restore(dict(view, invented_property="x"), control, "now")))
    ok("a type with no view is refused",
       refuses(lambda: project({"type": "relationship", "id": "relationship--x"})))
    ok("an unknown type is refused",
       refuses(lambda: restore({"type": "x-nonesuch"}, control, "now")))
    ok("a view whose type contradicts the committed object is refused",
       refuses(lambda: restore(dict(view, type="x-regulation"), control, "now")))

    # Editing a property that decides the path and SecID renames the object, which
    # would write one object's content over another's identifier.
    for prop in ("framework", "framework_version", "control_identifier"):
        ok(f"editing {prop} is refused — it names a different object",
           refuses(lambda p=prop: restore(dict(view, **{p: "other"}), control, "now")))

    # `source` decides which file gets written and arrives inside the view, so it is
    # the one field that could point the tool at something it has no business editing.
    ok("an absolute source path is refused",
       refuses(lambda: resolve_target("/tmp/evil.json")))
    ok("a traversing source path is refused",
       refuses(lambda: resolve_target("../../../tmp/evil.json")))
    ok("escaping and re-entering the repo is refused",
       refuses(lambda: resolve_target("objects/../README.md")))
    ok("a path inside the repo but outside objects/ is refused",
       refuses(lambda: resolve_target("schemas/x-control.json")))
    ok("a path under objects/ is accepted",
       resolve_target("objects/x-control/a.json").name == "a.json")

    # YAML's scalar resolution is the trap the format brings with it.
    ok("an unquoted `no` is caught as a boolean, not written as one",
       coercions({"status": False}) != [])
    ok("an unquoted timestamp is caught as a date",
       coercions({"valid_from": datetime.date(2026, 6, 22)}) != [])
    ok("a bare number is caught", coercions({"framework_version": 1.1}) != [])
    ok("a null is caught", coercions({"domain": None}) != [])
    ok("ordinary text is not flagged", coercions({"name": "Training Pipeline Security"}) == [])

    # An edit here is never durable on its own, and a tool that lets it look durable
    # has misled the person using it.
    note = durability_note(control, "objects/x-control/cloudsecurityalliance.org/"
                                    "aicm/1.1.0/TST-01.json")
    ok("a write says the edit will be overwritten", "overwritten" in note)
    ok("a write names the generator that will overwrite it",
       "tools/generate_aicm_controls.py" in note)
    ok("a write gives both remedies, upstream and conversion",
       "upstream" in note and "fix the generator" in note)
    unknown = durability_note(dict(control, framework_namespace="nowhere.example"),
                              "objects/x-control/nowhere.example/x/1/A.json")
    ok("an unmapped framework still warns, without naming a generator",
       "a generator in tools/" in unknown)

    # The schema is the contract, and --write applies it before writing.
    schemas = load_schemas()
    ok("a value the schema rejects is refused before writing",
       refuses(lambda: restore(dict(view, status="alive"), control, "now", schemas=schemas)))
    ok("a valid edit passes the schema",
       restore(dict(view, domain="Logging and Monitoring"), control,
               "2026-08-11T00:00:00.000Z", schemas=schemas)["domain"]
       == "Logging and Monitoring")

    bad = [label for label, passed in results if not passed]
    for label, passed in results:
        print(f"  {'ok  ' if passed else 'FAIL'} {label}")
    print(f"\n{len(results) - len(bad)}/{len(results)} view self-tests passed")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="an object to view, or a view to write back")
    ap.add_argument("--write", action="store_true",
                    help="treat the path as an edited view and write the JSON object")
    ap.add_argument("--check", action="store_true",
                    help="round-trip every committed object and require byte equality")
    ap.add_argument("--self-test", action="store_true",
                    help="check the round trip against messy text, edits, and refusals")
    ap.add_argument("--objects", default=str(ROOT / "objects"),
                    help="objects directory (default: objects)")
    ap.add_argument("--now", help="timestamp for a changed object "
                                  "(default: the current UTC time)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.check:
        paths = [pathlib.Path(p) for p in
                 sorted(glob.glob(os.path.join(args.objects, "**", "*.json"),
                                  recursive=True))]
        if not paths:
            sys.exit(f"no objects found under {args.objects}")
        checked, skipped, blocks, failures = check(paths)
        for path, why in failures:
            print(f"FAIL {os.path.relpath(path, ROOT)}\n     {why}")
        print(f"\n{checked - len(failures)}/{checked} objects round-tripped byte-identically "
              f"({skipped} generated objects have no view)")
        print(f"{blocks} prose properties rendered as readable blocks rather than quoted")
        return 1 if failures else 0

    if not args.path:
        ap.error("a path is required unless --check is given")
    path = pathlib.Path(args.path)

    if not args.write:
        print(to_yaml(json.loads(path.read_text()), source=path), end="")
        return 0

    try:
        view = yaml.safe_load(path.read_text())
    except yaml.YAMLError as err:
        # Indentation is significant, so a whitespace slip is a syntax error rather
        # than a cosmetic one. Report where, since that is the whole difficulty.
        where = getattr(err, "problem_mark", None)
        sys.exit(f"{path} is not valid YAML"
                 + (f" at line {where.line + 1}, column {where.column + 1}" if where else "")
                 + f":\n{getattr(err, 'problem', err)}")
    if not isinstance(view, dict):
        sys.exit(f"{path} does not hold a single object")
    target = view.get("source")
    if not target:
        sys.exit("the view has no `source:` line saying which object it edits")
    target = resolve_target(target)
    if not target.exists():
        sys.exit(f"{target} does not exist. The view corrects a committed object; "
                 "a new object comes from a generator in this directory.")

    committed = json.loads(target.read_text())
    now = args.now or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # Validated against the schema before anything is written: the point of the view
    # is that a person edits it, so the edit is exactly where a bad value enters.
    rebuilt = restore(view, committed, now, schemas=load_schemas())
    obj, state = reconcile(rebuilt, target)
    if state == "unchanged":
        print(f"{os.path.relpath(target, ROOT)}: unchanged")
        return 0
    target.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    print(f"{os.path.relpath(target, ROOT)}: {state}")
    # Say what moved. A property can be legitimately removed — the schema requires
    # few of them — but a removal is the edit most easily made by accident, and an
    # unreported one looks identical to no edit at all.
    for prop in sorted(set(committed) | set(obj)):
        if prop == "modified" or committed.get(prop) == obj.get(prop):
            continue
        if prop not in obj:
            print(f"  removed {prop}")
        elif prop not in committed:
            print(f"  added   {prop}")
        else:
            print(f"  changed {prop}")
    print()
    print(durability_note(obj, target))
    return 0


def durability_note(obj, path):
    """Why this edit is not durable on its own, and where the durable fix is.

    Every object under objects/ is generated. reconcile() preserves `id` and
    `created` and takes all content from the generator, so an edit made here is
    overwritten the next time that generator runs — silently, and looking exactly
    like no edit at all. A contributor who corrects a typo and watches it vanish a
    release later has been misled by this tool, which is worse than not having it.

    So a write says so. The two remedies are genuinely different and only the caller
    knows which applies: if the publisher's data is wrong the fix is upstream, and
    the catalog deliberately does not tidy a publisher's data in transit
    (CONVENTIONS-STIX-MODELING.md section 10); if the conversion is wrong the fix is
    the generator.
    """
    generator = generated_by(obj, os.path.relpath(path, ROOT))
    named = f"by {generator}" if generator else "by a generator in tools/"
    return (
        f"NOTE: this object is generated {named}, and an edit here is overwritten\n"
        f"the next time that generator runs. Nothing under objects/ is hand-authored.\n"
        f"To make this correction durable:\n"
        f"  - if the published source is wrong, raise it there — the catalog does not\n"
        f"    tidy a publisher's data in transit (conventions section 10), so the fix\n"
        f"    belongs upstream and the conversion follows it;\n"
        f"  - if the conversion is wrong, fix the generator and regenerate.\n"
        f"Editing here is still useful for seeing the corrected object, and for\n"
        f"checking what a generator change should produce.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
