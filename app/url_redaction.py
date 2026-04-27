# Ported from appevidence/evidence-capture-app at commit b4ec9dacccc3c3deb4c7c080c3b504a433790f4c
from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

REDACT_PARAMS: frozenset[str] = frozenset(
    {
        "token",
        "key",
        "password",
        "secret",
        "api_key",
        "apikey",
        "access_token",
        "auth",
        "code",
        "client_secret",
        "private_key",
        "passwd",
        "pass",
        "pwd",
        "credential",
        "credentials",
        "authorization",
    }
)

_REDACTED = "[REDACTED]"


def redact_url(url: str) -> str:
    """Redact sensitive query parameters from a URL."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        redacted = {k: [_REDACTED] if k.lower() in REDACT_PARAMS else v for k, v in params.items()}
        new_query = urlencode(redacted, doseq=True, safe="[]")
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url


def redact_auth_from_url(url: str) -> str:
    """Strip userinfo (user:pass@) from a URL."""
    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return url


def redact_url_for_log(url: str) -> str:
    """Apply both auth stripping and query param redaction."""
    return redact_url(redact_auth_from_url(url))
