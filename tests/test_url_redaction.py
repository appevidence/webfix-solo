# Ported from appevidence/evidence-capture-app at commit b4ec9dacccc3c3deb4c7c080c3b504a433790f4c
from __future__ import annotations

from app.url_redaction import REDACT_PARAMS, redact_auth_from_url, redact_url, redact_url_for_log


def test_redact_url_removes_token():
    url = "https://example.com/page?token=secret123&q=hello"
    result = redact_url(url)
    assert "secret123" not in result
    assert "[REDACTED]" in result
    assert "q=hello" in result


def test_redact_url_removes_api_key():
    url = "https://example.com/api?api_key=mykey&format=json"
    result = redact_url(url)
    assert "mykey" not in result
    assert "format=json" in result


def test_redact_url_no_sensitive_params():
    url = "https://example.com/page?q=hello&lang=en"
    result = redact_url(url)
    assert result == url


def test_redact_url_multiple_sensitive():
    url = "https://example.com/?token=abc&password=xyz&q=safe"
    result = redact_url(url)
    assert "abc" not in result
    assert "xyz" not in result
    assert "safe" in result


def test_redact_auth_from_url_strips_userinfo():
    url = "https://user:pass@example.com/path"
    result = redact_auth_from_url(url)
    assert "user" not in result
    assert "pass" not in result
    assert result == "https://example.com/path"


def test_redact_auth_from_url_no_auth():
    url = "https://example.com/path?q=1"
    assert redact_auth_from_url(url) == url


def test_redact_url_for_log_combines():
    url = "https://admin:password@example.com/?token=secret&q=safe"
    result = redact_url_for_log(url)
    assert "admin" not in result
    assert "secret" not in result
    assert "safe" in result


def test_redact_params_set():
    assert "token" in REDACT_PARAMS
    assert "password" in REDACT_PARAMS
    assert "api_key" in REDACT_PARAMS
