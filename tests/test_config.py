# Ported from appevidence/evidence-capture-app at commit c59d756a4cdb2f40d0b9a3570f411880d2df1c4c
from __future__ import annotations

import os
from unittest.mock import patch

from app.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.capture_timeout == 60
    assert s.capture_headless is True
    assert s.tsa_url == "http://timestamp.digicert.com"
    assert s.log_level == "INFO"
    assert s.max_retries == 3
    assert s.capture_viewport_width == 1280
    assert s.capture_viewport_height == 800


def test_settings_from_env():
    with patch.dict(os.environ, {"WEBFIX_CAPTURE_TIMEOUT": "120", "WEBFIX_LOG_LEVEL": "DEBUG"}):
        s = Settings()
        assert s.capture_timeout == 120
        assert s.log_level == "DEBUG"


def test_no_web_only_fields():
    s = Settings()
    # Ensure web-framework-specific settings are NOT present
    assert not hasattr(s, "trusted_proxies")
    assert not hasattr(s, "session_secret")
    assert not hasattr(s, "csrf_secret")
    assert not hasattr(s, "rate_limit")
    assert not hasattr(s, "otel_endpoint")


def test_resolved_paths():
    s = Settings()
    assert s.resolved_db_path == s.data_dir / "db.sqlite"
    assert s.resolved_signing_key_path == s.data_dir / "keys/signing.key"
    assert s.resolved_bundles_dir == s.data_dir / "bundles"
    assert s.resolved_audit_log_path == s.data_dir / "audit.log"
