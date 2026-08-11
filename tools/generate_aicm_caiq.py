#!/usr/bin/env python3
"""Generate CAIQ question objects and their links to the controls they assess.

Run against the AI-CAIQ JSON distribution, after the matching AICM controls have
been generated:

    python3 tools/generate_aicm_caiq.py path/to/aicm-caiq-1.1.0.json

A CAIQ question is an x-control in a questionnaire framework, not a separate
object type — see SCHEMA-STIX-OBJECT-EXTENSIONS.md. Each question is linked to the
control it assesses by a standard derived-from relationship, read left to right:
the question is derived from the control.

The source embeds a full copy of each parent control alongside every question.
That copy is deliberately not carried. The control is already an object, and
duplicating it would create a second copy to keep in step — the relationship says
which control a question belongs to, and the control says the rest.

Like the controls generator, re-running is safe: identifiers and created
timestamps are read back from the committed files and preserved.
"""

import argparse
import datetime
import json
import pathlib
import sys
import uuid

from catalog import (CONTROL_EXT, CSA_IDENTITY, KEY_ORDER, NAMESPACE, TLP_WHITE,
                     emit, order, report)

FRAMEWORK = "aicm-caiq"
PARENT_FRAMEWORK = "aicm"

# A question carries fewer properties than a control, not different ones, so both
# order against the one x-control list — see catalog.KEY_ORDER.
QUESTION_KEYS = KEY_ORDER["x-control"]
LINK_KEYS = KEY_ORDER["relationship"]


def build_question(q, version, published, now):
    qid = q["question_id"]
    return order({
        "type": "x-control",
        "spec_version": "2.1",
        "id": f"x-control--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "extensions": {CONTROL_EXT: {"extension_type": "new-sdo"}},
        "created_by_ref": CSA_IDENTITY,
        # A question has an identifier and a question, but no title. The question
        # text is the substantive requirement and goes in specification; name
        # carries a citation the catalog constructs, which is the same fallback
        # used for a source whose text may not be reproduced.
        "name": f"AICM-CAIQ {version} {qid}",
        "framework_namespace": NAMESPACE,
        "framework": FRAMEWORK,
        "framework_version": version,
        "control_identifier": qid,
        "domain": q["aicm_domain_title"],
        "status": "live",
        "valid_from": published,
        "specification": q["question"],
        "external_references": [{
            "source_name": "secid",
            "external_id": f"secid:control/{NAMESPACE}/{FRAMEWORK}@{version}#{qid}",
        }],
    }, QUESTION_KEYS)


def build_link(question_id, control_id, now):
    return order({
        "type": "relationship",
        "spec_version": "2.1",
        "id": f"relationship--{uuid.uuid4()}",
        "created": now,
        "modified": now,
        "object_marking_refs": [TLP_WHITE],
        "created_by_ref": CSA_IDENTITY,
        "relationship_type": "derived-from",
        "source_ref": question_id,
        "target_ref": control_id,
    }, LINK_KEYS)


def committed_controls(objects, version):
    """Map control identifier to the id of its already-committed object.

    The parent controls must exist before the questions that assess them, because
    a relationship names its target by identifier and that identifier is only
    settled once the control is committed.
    """
    root = (pathlib.Path(objects) / "x-control" / NAMESPACE
            / PARENT_FRAMEWORK / version)
    if not root.is_dir():
        sys.exit(f"no committed {PARENT_FRAMEWORK} {version} controls at {root}; "
                 f"generate them first")
    found = {}
    for path in sorted(root.glob("*.json")):
        obj = json.loads(path.read_text())
        found[obj["control_identifier"]] = obj["id"]
    return found


def published_date(source, data):
    """The release date, from the questions file or its sibling metadata."""
    if data.get("published"):
        return data["published"]
    sibling = source.with_name(source.stem + "-metadata.json")
    if sibling.exists():
        published = json.loads(sibling.read_text()).get("lifecycle", {}).get("published")
        if published:
            return published
    sys.exit(f"no publication date in {source.name} or a sibling metadata file; "
             f"pass --published")


def self_test():
    """Confirm question text is carried through untouched, as published."""
    messy = ("Are policies  established, documented,\r\napproved,\n"
             "communicated, applied — and “maintained”? ")
    q = {"question_id": "TST-01.1", "question": messy,
         "aicm_control_id": "TST-01", "aicm_domain_title": "Audit & Assurance"}
    obj = build_question(q, "1.1.0", "2026-06-22T00:00:00.000Z",
                         "2026-01-15T00:00:00.000Z")
    checks = [
        ("question text carried verbatim", obj["specification"], messy),
        ("name is a constructed citation", obj["name"], "AICM-CAIQ 1.1.0 TST-01.1"),
        ("domain carried verbatim", obj["domain"], "Audit & Assurance"),
        ("secid uses the questionnaire framework", obj["external_references"][0]["external_id"],
         "secid:control/cloudsecurityalliance.org/aicm-caiq@1.1.0#TST-01.1"),
        ("text survives the JSON round-trip",
         json.loads(json.dumps(obj, ensure_ascii=False))["specification"], messy),
    ]
    link = build_link(f"x-control--{uuid.uuid4()}", f"x-control--{uuid.uuid4()}",
                      "2026-01-15T00:00:00.000Z")
    # derived-from reads left to right: the question is derived from the control.
    checks.append(("link points question to control", link["relationship_type"],
                   "derived-from"))
    # The parent control is referenced, never copied.
    checks.append(("no embedded copy of the parent control",
                   [k for k in obj if k.startswith("aicm_")], []))

    bad = 0
    for label, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            print(f"       expected {want!r}\n       got      {got!r}")
    print(f"\n{len(checks) - bad}/{len(checks)} generator self-tests passed")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", help="the AI-CAIQ JSON distribution")
    ap.add_argument("--out", default="objects",
                    help="objects directory (default: objects)")
    ap.add_argument("--published", help="release date, if the source omits it")
    ap.add_argument("--now", help="timestamp for newly minted objects "
                                  "(default: the current UTC time)")
    ap.add_argument("--self-test", action="store_true",
                    help="check that a publisher's text is carried untouched")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.source:
        ap.error("a source is required unless --self-test is given")

    now = args.now or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    source = pathlib.Path(args.source)
    data = json.loads(source.read_text())
    version = data["caiq_version"]
    parent_version = data["aicm_version"]
    published = f"{args.published or published_date(source, data)}T00:00:00.000Z"

    controls = committed_controls(args.out, parent_version)
    missing = sorted({q["aicm_control_id"] for q in data["questions"]}
                     - set(controls))
    if missing:
        sys.exit(f"{len(missing)} question(s) name a control with no committed "
                 f"object: {', '.join(missing[:5])}")

    questions = pathlib.Path(args.out) / "x-control" / NAMESPACE / FRAMEWORK / version
    links = (pathlib.Path(args.out) / "relationship" / "derived-from"
             / NAMESPACE / FRAMEWORK / version)

    q_tally = emit((questions / f"{q['question_id']}.json",
                    build_question(q, version, published, now))
                   for q in data["questions"])
    report(f"{FRAMEWORK} {version} questions", questions, q_tally)

    # The link is minted only after the question object exists, so it can name the
    # committed identifier rather than one this run happened to generate.
    l_tally = emit((links / f"{q['question_id']}.json",
                    build_link(
                        json.loads((questions / f"{q['question_id']}.json").read_text())["id"],
                        controls[q["aicm_control_id"]], now))
                   for q in data["questions"])
    report(f"{FRAMEWORK} {version} derived-from links", links, l_tally)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
