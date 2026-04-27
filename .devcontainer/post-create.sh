#!/usr/bin/env bash
# Codespaces / devcontainer post-create bootstrap for webfix-solo.
# Idempotent: safe to re-run.
set -euo pipefail

echo ">>> webfix-solo: upgrading pip"
python -m pip install --upgrade pip

echo ">>> webfix-solo: installing project (editable) with [dev,ots] extras"
pip install -e ".[dev,ots]"

echo ">>> webfix-solo: installing Playwright Chromium browser + OS deps"
# --with-deps pulls in the apt packages Chromium needs (libnss3, etc.)
# Falls back to a plain install if --with-deps fails (e.g. no sudo).
python -m playwright install --with-deps chromium \
  || python -m playwright install chromium

echo ">>> webfix-solo: smoke test"
webfix --version
pytest -q || true

echo ">>> webfix-solo: ready. Try:  webfix --help"
