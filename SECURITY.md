# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities **privately** via GitHub's
["Report a vulnerability"](https://github.com/appevidence/webfix-solo/security/advisories/new) flow.
Do **not** open a public issue.

We aim to acknowledge reports within 5 business days.

## Scope

`webfix-solo` is a **single-user, local-only** CLI. The threat model is correspondingly narrow:

- Confidentiality and integrity of locally stored Ed25519 private keys (passphrase-protected at rest).
- Integrity of captured bundles (SHA-256 of every artifact, Ed25519-signed manifest).
- Tamper-evidence of the local hash-chained audit log.
- Safe handling of attacker-controlled URLs and page content during Playwright capture.

**Out of scope:** anything implying a server, network listener, multi-user access control, or remote attestation. Those concerns belong to Repo A / Repo B; see the "Related projects" section in the README.

## Cryptographic dependencies

- `cryptography` (X.509, hashing)
- `PyNaCl` (Ed25519)
- `rfc3161-client` (RFC 3161 timestamping)
- `opentimestamps-client` (optional `[ots]` extra)

We track upstream advisories via Dependabot and GitHub's advisory database.
