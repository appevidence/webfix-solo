# Ported from appevidence/evidence-capture-app at commit 874d3479e33d213c84107240921f2d9ae30a9543
from __future__ import annotations

import hashlib
from pathlib import Path

from app.hashing import hash_bytes, hash_file, hash_file_with_size


def test_hash_bytes_known():
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert hash_bytes(data) == expected


def test_hash_bytes_empty():
    assert hash_bytes(b"") == hashlib.sha256(b"").hexdigest()


def test_hash_file(tmp_path: Path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"test data")
    expected = hashlib.sha256(b"test data").hexdigest()
    assert hash_file(f) == expected


def test_hash_file_with_size(tmp_path: Path):
    data = b"some content"
    f = tmp_path / "test.bin"
    f.write_bytes(data)
    digest, size = hash_file_with_size(f)
    assert digest == hashlib.sha256(data).hexdigest()
    assert size == len(data)


def test_hash_file_large(tmp_path: Path):
    # Larger than CHUNK_SIZE (65536)
    data = b"x" * 200_000
    f = tmp_path / "large.bin"
    f.write_bytes(data)
    digest, size = hash_file_with_size(f)
    assert digest == hashlib.sha256(data).hexdigest()
    assert size == 200_000
