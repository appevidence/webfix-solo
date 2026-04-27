# Ported from appevidence/evidence-capture-app at commit 9392d282a7eb156d297c77928a333a6a0fe5c29c
from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


def slugify(text: str, max_len: int = 80) -> str:
    """Convert text/URL to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^\w\s-]", "-", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text[:max_len]


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it does not exist, return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(url: str) -> str:
    """Derive a safe filename from a URL."""
    parsed = urlparse(url)
    host = parsed.netloc or "unknown"
    path = parsed.path.strip("/").replace("/", "_") or "index"
    name = f"{host}_{path}"
    name = re.sub(r"[^\w.-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name[:100] or "capture"


def format_bytes(n: int) -> str:
    """Return human-readable byte size string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n //= 1024
    return f"{n:.1f} PB"
