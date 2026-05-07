# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The working surface for the CSA **Security Controls Catalog (CSA-CC)** working group, one of six WGs under CSA's **Compliance Automation Revolution (CAR)** initiative. The WG's mandate is to maintain a canonical, machine-readable catalog of cloud and technology-agnostic security controls aligned with CCM, AICM, IoT security, OSCAL, and (per the in-progress design below) STIX 2.1.

WG leadership: Andy Ruth, Daniele Catteddu, Larry Hughes.
Public WG page: https://cloudsecurityalliance.org/research/working-groups/security-controls-catalog

## Status: pre-content

As of this writing the repo tracks only `LICENSE.txt`. There is no source code, build system, schema files, or instance data committed. Do not assume directory conventions — read the current tree before writing files, and propose layout to the maintainer rather than inventing one.

Schemas are **exploratory / research status** and explicitly provisional. Do not treat any schema sketch (including the one summarized below) as normative. Always consult the current source-of-truth document before editing or generating instance data.

## Data model (provisional)

The catalog is being designed as a graph of four custom STIX 2.1 SDO types, related via the standard STIX `relationship` SRO so the data flows unchanged through existing STIX/TAXII servers, CTI platforms, and graph stores:

| Object | Role |
|---|---|
| `x-control` | Canonical CSA control definition (domain, ID, specification, ownership, lifecycle, applicability, threat mitigation, mappings, guidance) |
| `x-control-implementation` | Technical implementation unit — specific config/IaC/procedure that fulfills one or more controls |
| `x-regulatory-reference` | Clause or requirement from an external framework (ISO 27001, GDPR, NIST 800-53, etc.) |
| `x-control-assessment` | Outcome of a self-assessment, audit, or STAR/CAIQ evaluation against a control |

Current source of truth for field-level schemas: the design doc *"STIX Object Extensions for CSA Security Control Catalog (CSA-SCC)"* by Kurt Seifried (Google Doc, last updated 2025-11-20). Ask the maintainer for access; do not reproduce schema details from memory.

## Load-bearing design principles

These are the principles future contributions must respect — violating them is a category error, not a style nit:

- **Minimal invention.** Introduce new `x-*` types or properties only when CSA-CC concepts cannot be expressed with existing STIX 2.1 objects, vocabularies, or relationships. Prefer standard STIX over bespoke structures.
- **Alignment over replacement.** This work does **not** replace OSCAL and is **not** a universal GRC schema. Do not propose schemas that compete with OSCAL — propose ones that interoperate with it.
- **Maximum STIX compatibility.** No changes to STIX wire format, versioning, or transport. Custom SDOs use standard STIX properties (`id`, `created`, `modified`, `created_by_ref`, `labels`, `external_references`, etc.) and participate in relationships exactly like any other SDO.
- **Graph-first, not platform-specific.** No assumptions about storage engines, query languages, or UI conventions beyond what STIX-aware platforms already provide.
- **Forward compatibility.** When STIX adds new SDOs/SCOs, CSA-CC objects relate to them via the standard `relationship` SRO with no schema changes.

## Adjacent ecosystems CSA-CC must interoperate with

When making design or mapping decisions, keep these in scope:

- **CSA frameworks and artifacts**: CCM, AICM, IoT security initiatives, STAR/CAIQ, *Top Threats to Cloud Computing* annual report (controls should be expressible as "mitigates threat X" against the current threat list)
- **Standards**: STIX 2.1, OSCAL, MITRE ATT&CK (via `attack-pattern`)
- **External regulatory frameworks** modeled via `x-regulatory-reference` (ISO 27001, GDPR, NIST 800-53, etc.)

## Workflow

This is a public CSA repository. External collaboration uses the standard fork + PR model. Do not push directly to `main`; create a branch and open a PR for any change.

The `LICENSE.txt` reflects CSA's standard publication terms (no modification or redistribution of the *published* catalog). Repository-level collaboration via fork/PR is the accepted workflow regardless — treat the license as governing downstream consumption of releases, not the development process.

## Build / lint / test

None yet. When schema validation, OSCAL conversion, or STIX bundle generation tooling is added, document the commands here.
