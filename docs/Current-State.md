# Current State

`webfix-solo` is being bootstrapped as **Repo C** of the evidence-capture three-repo split.
The CLI surface is fully wired up (run `webfix --help`); the underlying modules are being
ported from Repo A (`appevidence/evidence-capture-app`) with the web layer stripped out.

This document tracks port progress. PRs that move an item from `[ ]` to `[x]` should
reference the source commit SHA in Repo A.

## Core (must port)

- [ ] `app/capture.py` — Playwright capture (HTML, screenshot, PDF, HAR)
- [ ] `app/hashing.py` — SHA-256 of artifacts
- [ ] `app/manifest.py` — bundle manifest schema + builder
- [ ] `app/signing.py` — Ed25519 sign / verify
- [ ] `app/timestamping/` — RFC 3161 client wrapper
- [ ] `app/verify.py` — bundle verification (signature + hashes + timestamp chain)
- [ ] `app/audit.py` — hash-chained audit log
- [ ] `app/audit_admin.py` — wired into `webfix audit list|verify|verify-all`
- [ ] `app/url_redaction.py` — URL redaction in audit-log entries
- [ ] `app/export.py` — extract bundle contents
- [ ] `app/report.py` + `app/fonts/` — PDF report (reportlab)
- [ ] `app/database.py` + `app/db_models.py` — **simplified to SQLite-only**;
      use `Base.metadata.create_all` instead of Alembic
- [ ] `app/config.py` — pruned to local-only options (no `TRUSTED_PROXIES`,
      no session/CSRF/Basic-auth knobs, no rate-limit knobs, no OTel knobs)
- [ ] `app/models.py`, `app/metadata.py`, `app/http_utils.py`, `app/retry.py`,
      `app/utils.py`

## Optional extras (port behind feature flags)

- [ ] `app/wayback.py` — `--with-wayback`
- [ ] `app/blockchain.py` — `--with-ots` (default extra) and `--with-eth` (`[eth]` extra)

## Explicitly **not** ported (web layer; belongs to Repo A / B)

- `app/main.py` (FastAPI app + lifespan)
- `app/routers/`, `app/templates/`, `app/static/`
- `app/auth.py`, `app/session_auth.py`, `app/session_capture.py`, `app/csrf.py`,
  `app/limiter.py`, `app/browser_pool.py`, `app/observability.py`
- `Dockerfile`, `Dockerfile.verifier`, `docker-compose.yml`, `.dockerignore`
- `alembic/`, `alembic.ini`
- `tests/test_security_headers.py`, `tests/test_csrf*.py`, `tests/test_session_*.py`,
  `tests/test_routers_*.py`, `tests/test_browser_pool*.py`, `tests/test_main_*.py`,
  `tests/test_observability*.py`
- `docs/wiki/Deployment.md`, `docs/business/`, `docs/BACKLOG-Platform.md`,
  `docs/audits/`, `.github/workflows/wiki-sync.yml`, `scripts/render_wiki.py`

## Dependencies removed vs. Repo A

Excluded from `pyproject.toml`: `fastapi`, `starlette`, `uvicorn`, `python-multipart`,
`slowapi`, `jinja2`, `prometheus-fastapi-instrumentator`, `opentelemetry-*`, `alembic`,
`eth-account`, `eth-abi`, `eth-keyfile`, `eth-keys`, `eth-rlp`, `eth-utils`, `eth-typing`,
`eth-hash`, `rlp`, `hexbytes`, `ckzg`, `bitarray`, `pycryptodome`, `parsimonious`, `regex`.
The Ethereum stack moves into the `[eth]` optional extra (`web3`).
