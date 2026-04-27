# Ported from appevidence/evidence-capture-app at commit 7b6f386d7e55a98b117d32c7103315abfa755ad0
from __future__ import annotations

import hashlib
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from app.export import BundleContents, export_bundle, extract_bundle
from app.manifest import build_manifest, manifest_to_json
from app.models import ArtifactHash


def _make_bundle(tmp_path: Path) -> Path:
    html_content = b"<html><body>Test</body></html>"
    html_hash = hashlib.sha256(html_content).hexdigest()
    artifacts = [ArtifactHash(filename="page.html", sha256=html_hash, size_bytes=len(html_content))]
    manifest = build_manifest(
        url="https://example.com",
        captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        user_agent="test/1.0",
        artifacts=artifacts,
    )
    bundle_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle_path, "w") as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
        zf.writestr("page.html", html_content)
    return bundle_path


def test_extract_bundle_returns_contents(tmp_path: Path):
    bundle_path = _make_bundle(tmp_path)
    contents = extract_bundle(bundle_path)
    assert isinstance(contents, BundleContents)
    assert contents.manifest.url == "https://example.com"
    assert contents.html == b"<html><body>Test</body></html>"
    assert contents.screenshot is None
    assert contents.pdf is None


def test_export_bundle_writes_files(tmp_path: Path):
    bundle_path = _make_bundle(tmp_path)
    out_dir = tmp_path / "extracted"
    paths = export_bundle(bundle_path, out_dir)
    assert any(p.name == "manifest.json" for p in paths)
    assert any(p.name == "page.html" for p in paths)
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "page.html").exists()
