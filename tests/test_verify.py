# Ported from appevidence/evidence-capture-app at commit e29a55188d3af69d5c7609301309ca3099bbde36
from __future__ import annotations

import hashlib
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from app.manifest import build_manifest, manifest_to_json, sign_manifest
from app.models import ArtifactHash
from app.signing import generate_keypair
from app.verify import verify_bundle


def _make_test_bundle(tmp_path: Path, sign: bool = True) -> tuple[Path, bytes | None]:
    """Create a minimal valid test bundle zip."""
    html_content = b"<html><body>Test</body></html>"
    html_hash = hashlib.sha256(html_content).hexdigest()

    artifacts = [
        ArtifactHash(filename="page.html", sha256=html_hash, size_bytes=len(html_content)),
    ]
    manifest = build_manifest(
        url="https://example.com",
        captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        user_agent="test/1.0",
        artifacts=artifacts,
    )

    priv_pem, pub_pem = generate_keypair()
    if sign:
        manifest = sign_manifest(manifest, priv_pem)

    bundle_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w") as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
        zf.writestr("page.html", html_content)

    return bundle_path, pub_pem if sign else None


def test_verify_valid_bundle(tmp_path: Path):
    bundle_path, _pub_pem = _make_test_bundle(tmp_path, sign=True)
    result = verify_bundle(bundle_path)
    assert result.ok, f"Expected ok, got errors: {result.errors}"


def test_verify_bundle_with_public_key(tmp_path: Path):
    bundle_path, pub_pem = _make_test_bundle(tmp_path, sign=True)
    result = verify_bundle(bundle_path, public_key_pem=pub_pem)
    assert result.ok, f"Expected ok, got errors: {result.errors}"


def test_verify_missing_file():
    result = verify_bundle(Path("/nonexistent/bundle.zip"))
    assert not result.ok
    assert any("not found" in e for e in result.errors)


def test_verify_tampered_artifact(tmp_path: Path):
    """Tamper with an artifact after signing — should fail hash check."""
    bundle_path, _ = _make_test_bundle(tmp_path, sign=True)

    # Re-pack with tampered HTML
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle_path, "r") as orig, zipfile.ZipFile(tampered, "w") as new_zf:
        for name in orig.namelist():
            if name == "page.html":
                new_zf.writestr(name, b"<html>TAMPERED</html>")
            else:
                new_zf.writestr(name, orig.read(name))

    result = verify_bundle(tampered)
    assert not result.ok
    assert any("mismatch" in e.lower() for e in result.errors)


def test_verify_unsigned_bundle(tmp_path: Path):
    bundle_path, _ = _make_test_bundle(tmp_path, sign=False)
    result = verify_bundle(bundle_path)
    assert result.ok  # No signature = no signature error, just no verification
