# Current State

`webfix-solo` is **Repo C** of the evidence-capture three-repo split (the term
"Repo A" everywhere in this repo refers to the upstream
[`appevidence/evidence-capture-app`](https://github.com/appevidence/evidence-capture-app),
from which the core capture / signing / verify modules were ported with the web
layer removed). See the *Related projects* table in the root `README.md` for the
full A / B / C map.

The CLI surface (`webfix --help`) is fully wired to the ported modules under
`app/*`. PRs that move an item from `[ ]` to `[x]` should reference the source
commit SHA in Repo A (each ported module already carries a
`# Ported from appevidence/evidence-capture-app at commit …` header).

## CLI wiring (Repo C)

Every command is now a thin shell over a ported `app.*` module — no
sub-command exits with the legacy "not yet ported" message any more.

| Command            | Backed by                                                                |
|--------------------|--------------------------------------------------------------------------|
| `webfix init`      | `app.signing.generate_keypair`, `app.database.init_db`, `app.audit`      |
| `webfix capture`   | `app.capture.run_capture` + `app.audit` (URL is redacted before logging) |
| `webfix verify`    | `app.verify.verify_bundle` (exits 1 on hash/signature failure)           |
| `webfix export`    | `app.export.export_bundle`                                               |
| `webfix report`    | `app.report.render_report_from_bundle`                                   |
| `webfix audit …`   | `app.audit_admin` (`list`, `verify`, `verify-all`)                       |

`tests/test_cli.py` covers each of the above end to end (the `capture`
pipeline is exercised with a fake `run_capture` so the test suite does not
require a real browser).

## Core (must port)

- [x] `app/capture.py` — Playwright capture (HTML, screenshot, PDF, HAR)
- [x] `app/hashing.py` — SHA-256 of artifacts
- [x] `app/manifest.py` — bundle manifest schema + builder
- [x] `app/signing.py` — Ed25519 sign / verify
- [x] `app/timestamping/` — RFC 3161 client wrapper
- [x] `app/verify.py` — bundle verification (signature + hashes + timestamp chain)
- [x] `app/audit.py` — hash-chained audit log
- [x] `app/audit_admin.py` — wired into `webfix audit list|verify|verify-all`
- [x] `app/url_redaction.py` — URL redaction in audit-log entries
- [x] `app/export.py` — extract bundle contents
- [x] `app/report.py` + `app/fonts/` — PDF report (reportlab)
- [x] `app/database.py` + `app/db_models.py` — **simplified to SQLite-only**;
      use `Base.metadata.create_all` instead of Alembic
- [x] `app/config.py` — pruned to local-only options (no `TRUSTED_PROXIES`,
      no session/CSRF/Basic-auth knobs, no rate-limit knobs, no OTel knobs)
- [x] `app/models.py`, `app/metadata.py`, `app/http_utils.py`, `app/retry.py`,
      `app/utils.py`

## Optional extras (port behind feature flags)

- [ ] `app/wayback.py` — `--with-wayback`
- [ ] `app/blockchain.py` — `--with-ots` (default extra) and `--with-eth` (`[eth]` extra)

While these flags are not yet implemented, passing them to `webfix capture`
emits a yellow warning on stderr and the capture proceeds **without** the
requested extra, instead of failing.

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
