# Ported from appevidence/evidence-capture-app at commit a5e34bf4a387f77f339f2db6aa83e0f31f8234eb
from __future__ import annotations

import base64
import json
from datetime import datetime

from app.hashing import hash_bytes
from app.models import ArtifactHash, ManifestV1
from app.signing import private_key_to_public_pem, sign_bytes


def build_manifest(
    url: str,
    captured_at: datetime,
    user_agent: str,
    artifacts: list[ArtifactHash],
) -> ManifestV1:
    """Build a ManifestV1 from capture data."""
    return ManifestV1(
        url=url,
        captured_at=captured_at,
        user_agent=user_agent,
        artifacts=artifacts,
    )


def _canonical_dict(manifest: ManifestV1) -> dict:
    """Return the canonical dict (exclude hash/sig/key/timestamp fields)."""
    data = manifest.model_dump(mode="json")
    for key in ("manifest_hash", "signature_b64", "public_key_b64", "timestamp_info"):
        data.pop(key, None)
    return data


def compute_manifest_hash(manifest: ManifestV1) -> str:
    """Compute SHA-256 of the canonical JSON representation."""
    canonical = json.dumps(_canonical_dict(manifest), sort_keys=True, separators=(",", ":"))
    return hash_bytes(canonical.encode())


def sign_manifest(
    manifest: ManifestV1,
    private_key_pem: bytes,
    passphrase: bytes | None = None,
) -> ManifestV1:
    """Sign the manifest. Sets manifest_hash, signature_b64, public_key_b64."""
    manifest_hash = compute_manifest_hash(manifest)
    signature = sign_bytes(manifest_hash.encode(), private_key_pem, passphrase)
    public_key_pem = private_key_to_public_pem(private_key_pem, passphrase)
    return manifest.model_copy(
        update={
            "manifest_hash": manifest_hash,
            "signature_b64": base64.b64encode(signature).decode(),
            "public_key_b64": base64.b64encode(public_key_pem).decode(),
        }
    )


def manifest_to_json(manifest: ManifestV1) -> str:
    """Serialize manifest to pretty JSON."""
    return manifest.model_dump_json(indent=2)


def manifest_from_json(data: str | bytes) -> ManifestV1:
    """Deserialize manifest from JSON string or bytes."""
    if isinstance(data, bytes):
        data = data.decode()
    return ManifestV1.model_validate_json(data)
