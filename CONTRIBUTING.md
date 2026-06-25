# Contributing to the CSA Security Controls Catalog

Thank you for your interest in contributing. This guide explains how
contribution works here and what signing the Contributor License Agreement
(CLA) means.

## How contributions are made

1. Open an issue to discuss a change, or comment on an existing one.
2. Fork the repository and create a branch in your fork.
3. Open a pull request against `main`.
4. A maintainer reviews; once approved and the CLA check passes, we merge.

**Substantive contributions are accepted only via pull request.** If you
paste catalog content, mappings, or control text into an issue comment, a
maintainer will ask you to submit it as a pull request so that it is covered
by the CLA.

## The license and the CLA — two different things

Our [`LICENSE.txt`](LICENSE.txt) restricts what *consumers* may do with the
**published** catalog (personal, non-commercial use; no modification or
redistribution). Contributing through GitHub is governed differently:

- **GitHub's Terms of Service** give you the right to fork this public
  repository and submit pull requests.
- **The CLA** — not the license — is the agreement that governs what rights
  you grant CSA when you contribute.

In short: the license governs consumers of releases; the CLA governs
contributors.

## Signing the CLA

Signing happens entirely in GitHub, in the public **CSA CLA-Ledger**
([`CloudSecurityAlliance/CLA-Ledger`](https://github.com/CloudSecurityAlliance/CLA-Ledger)).
You sign **once for this project** — the Security Controls Catalog has its own
directory in the ledger, `security-controls-catalog/`, and your signature lives
there. (Coverage is per project: if you later contribute to a different CSA
project, you sign that project's CLA separately. See the ledger's
[README](https://github.com/CloudSecurityAlliance/CLA-Ledger#readme) for why,
and its [FAQ](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/FAQ.md)
for plain-English answers.)

### Step by step

The authoritative template and instructions live in the ledger at
[`security-controls-catalog/signatures/README.md`](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/security-controls-catalog/signatures/README.md).
The process is:

1. **Find your numeric GitHub account ID.** Your *login* can be renamed, so the
   ledger keys signatures to your permanent numeric ID. Look it up with:
   ```sh
   curl -s https://api.github.com/users/<your-login> | jq -r .id
   # no jq?  curl -s https://api.github.com/users/<your-login> | grep '"id"'
   ```
2. **Fork the ledger** —
   [`CloudSecurityAlliance/CLA-Ledger`](https://github.com/CloudSecurityAlliance/CLA-Ledger) —
   to your own account.
3. **Create your signature file** at
   `security-controls-catalog/signatures/<your-id>.md`, named for the numeric ID
   from step 1 (e.g. `583231.md`). You may only add your *own* file.
4. **Paste the full CLA text.** Copy the entire text of the current CLA version
   into your file. The ledger's
   [`signatures/README.md`](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/security-controls-catalog/signatures/README.md)
   is the authoritative guide — it names the version to sign and links its
   **frozen** text under
   [`security-controls-catalog/versions/`](https://github.com/CloudSecurityAlliance/CLA-Ledger/tree/main/security-controls-catalog/versions)
   (sign the frozen version file, not the mutable `CLA.md`). Your signature file
   is a complete, self-contained record of exactly what you agreed to.
5. **Append the signature block** from the template, filled in — your GitHub
   login, your numeric ID, the CLA version, and the date, with the statement
   that you agree to and sign the Agreement.
6. **Open a pull request from the same GitHub account** whose numeric ID you
   used as the filename. This matters: identity is taken from the authenticated
   account that opens the PR, not from git commit metadata.

### What happens next

An automated check (`validate-signature.yml`) confirms, against the account that
opened the PR, that: the filename is your numeric ID; the login and ID in your
file match that account; the version, date, and agreement statement are present;
and the CLA text you pasted matches the published version verbatim. A maintainer
then reviews it, and **CSA accepts your signature by merging the PR** — that
merge is the moment the Agreement takes effect (CSA accepts at its discretion).

Once your signature is merged, you're covered for your future contributions to
the Security Controls Catalog under the **current CLA version** — no need to
sign again unless the CLA *materially changes*, in which case you re-sign the
new version to keep contributing. From then on, when you open a contribution PR
*here*, the CLA check confirms you've signed the version the project currently
requires before the PR can proceed.

When you sign, in plain terms:

- **You keep ownership** — CSA takes a license, **not an assignment**, so you
  may continue to use, publish, or relicense your own work elsewhere.
- **You grant CSA an irrevocable license** — including the right to use your
  contribution in CSA's commercial offerings — to the contribution you
  submit here.
- **You confirm the work is yours to give** (or that you have permission),
  and that you are not knowingly submitting someone else's restricted
  material.

Why are CSA's rights broad while the published catalog is restricted? Short
version: broad rights let CSA **steward and evolve** the catalog, while
recipients get only what the published license allows. The CLA
[FAQ](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/FAQ.md)
explains this and other "why" questions.

Read the full text before signing:
[CSA Contributor License Agreement](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/security-controls-catalog/CLA.md).

When you sign, the record (your GitHub login and numeric account ID, the CLA
version, and the date) is your signature file in the public CSA CLA-Ledger. The
ledger's [privacy note](https://github.com/CloudSecurityAlliance/CLA-Ledger/blob/main/PRIVACY.md)
explains what signing records; for your data-protection rights and contact, see
the [CSA Privacy Notice](https://cloudsecurityalliance.org/legal/privacy-notice/).

If you are contributing on behalf of an employer who owns your work, make sure
you have your employer's authorization before you sign — by signing you confirm
you are entitled to grant these rights. If unsure, check with your employer or
contact info@cloudsecurityalliance.org.

## Working as a group, or with co-authors

Catalog work often starts as a group discussion — a call or a thread — that one
person then writes up and submits. That's fully supported, and in most cases
**only the person who writes and submits the contribution signs**:

- **Discussion and ideas don't require signing.** Copyright protects the
  *written expression*, not the underlying ideas, facts, or discussion. The
  person who authors the text of a contribution is its author; people who only
  contributed ideas in a discussion are **not** co-authors and do not need to
  sign. So when a CSA analyst or volunteer writes up a group discussion and
  submits it, that person signs — the others don't have to.
- **The author of record is the commit author.** Whoever is recorded as a
  commit's author must have signed — the CLA check verifies every commit author.
  By signing and submitting, you represent (per the CLA's representations) that
  you are entitled to grant the rights in the whole contribution, including any
  input you incorporated.
- **Genuine co-authorship.** If two or more people actually co-wrote the *text*
  of a contribution, each co-author signs the CLA — or you identify the portion
  that is not your original creation and submit it under the CLA's "submissions
  on behalf of others" provision.
- **`Co-authored-by:` trailers.** For a **human** co-author — someone who
  co-wrote the *text* — each must also sign the CLA; a credited human co-author
  who hasn't signed is a coverage gap the automated check can't see (it verifies
  commit *authors*, not trailers). An **AI assistant** may be credited as a
  co-author: it works at your direction, holds no rights, and cannot sign, so no
  signature is required — by committing, you take responsibility for the
  AI-assisted content, and your CLA and representations cover it as input you
  incorporated.

## AI-assisted contributions

AI-assisted contributions are welcome. You remain responsible for the
representations you make when you sign — in particular, that the contribution
is your original creation and that you have the right to submit it. Do not
submit material you cannot stand behind on those terms.

## Sources and third-party content

The catalog references and maps to external standards and regulations (ISO,
NIST, GDPR, and others), much of which is copyrighted. To keep contributions
clean and lawful:

- **Reference, don't reproduce.** Refer to external standards by their
  identifier (clause, control, or section ID) plus your own description. Do
  **not** paste the copyrighted text of a standard into a contribution —
  ISO/IEC standard text in particular must not be reproduced.
- **Declare your sources.** In the pull request, list the sources behind any
  mapping or claim so reviewers can verify provenance.
- **Original or authorized.** Confirm your contribution is your own wording,
  or that you have the right to submit any third-party material and have
  identified it as such. (This is part of what you affirm in the CLA.)

If you're unsure whether something can be included, ask in an issue first.

## Questions

Open an issue or contact the working group via the
[CSA Security Controls Catalog working group page](https://cloudsecurityalliance.org/research/working-groups/security-controls-catalog).
