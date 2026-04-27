# Ported from appevidence/evidence-capture-app at commit a5e34bf4a387f77f339f2db6aa83e0f31f8234eb
from __future__ import annotations

from datetime import UTC, datetime

from app.manifest import (
    build_manifest,
    compute_manifest_hash,
    manifest_from_json,
    manifest_to_json,
    sign_manifest,
)
from app.models import ArtifactHash
from app.signing import generate_keypair


def _make_artifacts() -> list[ArtifactHash]:
    return [
        ArtifactHash(filename="page.html", sha256="abc123", size_bytes=1024),
        ArtifactHash(filename="screenshot.png", sha256="def456", size_bytes=2048),
    ]


def test_build_manifest():
    now = datetime.now(UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    assert manifest.url == "https://example.com"
    assert manifest.captured_at == now
    assert len(manifest.artifacts) == 2
    assert manifest.version == "1"


def test_compute_manifest_hash_stable():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    h1 = compute_manifest_hash(manifest)
    h2 = compute_manifest_hash(manifest)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_compute_manifest_hash_excludes_sig_fields():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    h1 = compute_manifest_hash(manifest)
    # Adding a hash/signature should not change canonical hash
    manifest2 = manifest.model_copy(update={"manifest_hash": "old_hash", "signature_b64": "abc"})
    h2 = compute_manifest_hash(manifest2)
    assert h1 == h2


def test_sign_manifest():
    priv_pem, _pub_pem = generate_keypair()
    now = datetime.now(UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    signed = sign_manifest(manifest, priv_pem)
    assert signed.manifest_hash is not None
    assert signed.signature_b64 is not None
    assert signed.public_key_b64 is not None


def test_manifest_json_roundtrip():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    json_str = manifest_to_json(manifest)
    loaded = manifest_from_json(json_str)
    assert loaded.url == manifest.url
    assert loaded.user_agent == manifest.user_agent
    assert len(loaded.artifacts) == len(manifest.artifacts)


def test_manifest_from_json_bytes():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    manifest = build_manifest(
        url="https://example.com",
        captured_at=now,
        user_agent="test/1.0",
        artifacts=_make_artifacts(),
    )
    json_bytes = manifest_to_json(manifest).encode()
    loaded = manifest_from_json(json_bytes)
    assert loaded.url == manifest.url
