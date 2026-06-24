# CSA Security Controls Catalog

A canonical, machine-readable catalog of cloud and technology-agnostic
security controls, maintained by the Cloud Security Alliance (CSA) Security
Controls Catalog working group — Working Group 1 of CSA's **Compliance
Automation Revolution (CAR)** initiative.

> **Status: early-stage / research-grade.** The data model and schemas in
> this repository are **exploratory and provisional** and may change as
> implementation experience accumulates. Treat the custom STIX extensions as
> research-status, not a stable specification. Initial content is being
> prepared.

## What this is

The Security Controls Catalog expresses security controls — and their relationships to regulations,
implementations, assessments, threats, and attack patterns — as a graph, using
**STIX 2.1** with a small set of custom STIX Domain Objects:

| Object | Role |
|---|---|
| `x-control` | A canonical CSA control definition |
| `x-control-implementation` | A specific technical implementation of one or more controls |
| `x-regulatory-reference` | A clause or requirement from an external framework (ISO 27001, GDPR, NIST 800-53, …) |
| `x-control-assessment` | The outcome of an assessment or audit against a control |

These connect to each other and to the wider STIX graph (including MITRE
ATT&CK) through standard STIX relationships, so the data flows unchanged
through existing STIX/TAXII tools, CTI platforms, and graph stores. The
reasoning behind these choices is in
[`DESIGN-RATIONALE-STIX-EXTENSIONS.md`](DESIGN-RATIONALE-STIX-EXTENSIONS.md).

The catalog is designed to **interoperate with — not replace — OSCAL**, and to
align with CSA's CCM, AICM, and IoT security work.

## Who it's for

Cloud security and GRC practitioners, framework and tool builders, auditors,
and AI agents that need controls and their cross-framework mappings in a
structured, queryable form.

## Intended publication formats

STIX 2.1 (the back-end representation), OSCAL (for compliance/audit
consumers), and plain JSON, YAML, and spreadsheet exports. See the design
rationale for the reasoning.

## Using the catalog

The repository is the distribution channel — clone it, or consume tagged
releases. Catalog objects are identified using
[SecID](https://github.com/CloudSecurityAlliance/SecID), so they can also be
resolved through SecID's public resolver where applicable.

## Contributing

Contributions are welcome by fork and pull request. **All contributions
require a signed Contributor License Agreement (CLA)** — you sign the **current
CLA version** once for this project (re-signing only if the CLA materially
changes), by opening a pull request adding a signature file (containing the full
CLA text you agree to) to the CSA CLA-Ledger. It lets CSA include your
work in the catalog and CSA's broader offerings while you keep ownership of your
contribution. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how it works and what
signing means.

## Working group

The Security Controls Catalog working group operates under CSA's CAR initiative. Working group
information and how to participate:
<https://cloudsecurityalliance.org/research/working-groups/security-controls-catalog>.

## License

The published catalog is governed by [`LICENSE.txt`](LICENSE.txt). Note that
the license that governs *consuming* the published catalog and the CLA that
governs *contributing* to it are two different things — see `CONTRIBUTING.md`.
