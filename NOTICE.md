# NOTICE

`webfix-solo` is derived from [`appevidence/evidence-capture-app`](https://github.com/appevidence/evidence-capture-app)
("Repo A"), with the entire web layer (FastAPI / Starlette / Uvicorn / Jinja2 templates,
slowapi, OpenTelemetry/Prometheus instrumentation, session/CSRF/Basic-auth, browser pool,
Alembic migrations, Docker images) removed. Code that remains — Playwright capture,
SHA-256 hashing, Ed25519 signing, RFC 3161 timestamping, OpenTimestamps integration,
Wayback Machine submission, hash-chained audit log, verify, export, and PDF report —
is licensed under the MIT License of Repo A and continues under the MIT License of
this repository (see [`LICENSE`](LICENSE)).

This project is **not affiliated with, nor endorsed by**, any state or
inter-state cryptographic / certification authority.
