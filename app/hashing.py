# Ported from appevidence/evidence-capture-app at commit 874d3479e33d213c84107240921f2d9ae30a9543
from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 65536


def hash_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of data."""
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def hash_file_with_size(path: Path) -> tuple[str, int]:
    """Return (sha256_hex_digest, size_bytes) for a file."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size
