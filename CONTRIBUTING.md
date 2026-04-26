# Contributing to webfix-solo

Thanks for your interest! `webfix-solo` is intentionally small. Before opening a PR, please confirm the change fits the **Repo C scope**:

- ✅ single-user, local-only, CLI / desktop
- ✅ improvements to capture, hashing, signing, timestamping, audit log, verify, export, report
- ❌ HTTP server, multi-tenant, RBAC, OIDC, MFA, reverse-proxy concerns
- ❌ Docker / docker-compose run-targets
- ❌ Alembic migrations (we use `Base.metadata.create_all` on a local SQLite DB)

Web-app and platform features belong in Repo A and Repo B respectively — see the "Related projects" table in the README.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ots,wayback]"
playwright install chromium
pre-commit install
```

## Quality gates

Run before pushing:

```bash
pre-commit run --all-files
pytest -q
```

CI runs the same gates plus CodeQL (Python) on every PR.

## Commit style

Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
Keep commits surgical and focused; one logical change per commit.

## Porting from Repo A

Many modules under `app/` are stubs marked with `# TODO(port-from-A):`. When porting:

1. Copy the file from `appevidence/evidence-capture-app` at a pinned commit SHA.
2. Strip any FastAPI / Starlette / slowapi / OTel / template / session imports.
3. Replace any web-framework error handling with plain Python exceptions / Typer error exits.
4. Add or migrate tests under `tests/`.
5. Update [`docs/Current-State.md`](docs/Current-State.md) and reference the source SHA in the commit message.
