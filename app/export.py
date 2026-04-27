# Ported from appevidence/evidence-capture-app at commit 7b6f386d7e55a98b117d32c7103315abfa755ad0
from __future__ import annotations

import zipfile
from pathlib import Path

from pydantic import BaseModel

from app.manifest import manifest_from_json
from app.models import ManifestV1


class BundleContents(BaseModel):
    manifest: ManifestV1
    html: bytes | None = None
    screenshot: bytes | None = None
    pdf: bytes | None = None
    har: bytes | None = None
    signature: bytes | None = None

    model_config = {"arbitrary_types_allowed": True}


def extract_bundle(bundle_path: Path) -> BundleContents:
    """Extract a bundle zip file and return its contents."""
    with zipfile.ZipFile(bundle_path, "r") as zf:
        names = zf.namelist()

        manifest_json = zf.read("manifest.json")
        manifest = manifest_from_json(manifest_json)

        html = zf.read("page.html") if "page.html" in names else None
        screenshot = zf.read("screenshot.png") if "screenshot.png" in names else None
        pdf = zf.read("page.pdf") if "page.pdf" in names else None
        har = zf.read("capture.har") if "capture.har" in names else None
        signature = zf.read("signature.bin") if "signature.bin" in names else None

    return BundleContents(
        manifest=manifest,
        html=html,
        screenshot=screenshot,
        pdf=pdf,
        har=har,
        signature=signature,
    )


def export_bundle(bundle_path: Path, out_dir: Path) -> list[Path]:
    """Extract all files from a bundle zip into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(bundle_path, "r") as zf:
        for name in zf.namelist():
            zf.extract(name, out_dir)
            extracted.append(out_dir / name)
    return extracted
