# Ported from appevidence/evidence-capture-app at commit e29a55188d3af69d5c7609301309ca3099bbde36
from __future__ import annotations

import base64
import hashlib
import zipfile
from pathlib import Path

from app.export import extract_bundle
from app.manifest import compute_manifest_hash
from app.models import BundleVerificationResult
from app.signing import verify_signature
from app.timestamping import verify_timestamp


def verify_bundle(  # noqa: PLR0912
    bundle_path: Path,
    public_key_pem: bytes | None = None,
) -> BundleVerificationResult:
    """Verify a bundle zip: artifact hashes, signature, and optional timestamp."""
    errors: list[str] = []
    warnings: list[str] = []

    if not bundle_path.exists():
        return BundleVerificationResult(ok=False, errors=["Bundle file not found"])

    try:
        contents = extract_bundle(bundle_path)
    except Exception as exc:
        return BundleVerificationResult(ok=False, errors=[f"Failed to open bundle: {exc}"])

    manifest = contents.manifest

    # Verify artifact hashes
    with zipfile.ZipFile(bundle_path, "r") as zf:
        for artifact in manifest.artifacts:
            if artifact.filename not in zf.namelist():
                errors.append(f"Missing artifact: {artifact.filename}")
                continue
            data = zf.read(artifact.filename)
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != artifact.sha256:
                errors.append(
                    f"Hash mismatch for {artifact.filename}: "
                    f"expected {artifact.sha256}, got {actual_hash}"
                )
            if len(data) != artifact.size_bytes:
                errors.append(
                    f"Size mismatch for {artifact.filename}: "
                    f"expected {artifact.size_bytes}, got {len(data)}"
                )

    # Verify signature
    key_pem = public_key_pem
    if key_pem is None and manifest.public_key_b64:
        key_pem = base64.b64decode(manifest.public_key_b64)

    if manifest.signature_b64 and manifest.manifest_hash and key_pem:
        try:
            signature = base64.b64decode(manifest.signature_b64)
            verify_signature(manifest.manifest_hash.encode(), signature, key_pem)
        except Exception as exc:
            errors.append(f"Signature verification failed: {exc}")
    elif manifest.signature_b64 and not key_pem:
        warnings.append("Signature present but no public key available for verification")

    # Verify manifest hash consistency
    if manifest.manifest_hash:
        expected_hash = compute_manifest_hash(manifest)
        if expected_hash != manifest.manifest_hash:
            errors.append(
                f"Manifest hash mismatch: expected {expected_hash}, got {manifest.manifest_hash}"
            )

    # Verify RFC 3161 timestamp if present
    if manifest.timestamp_info and manifest.timestamp_info.token_b64:
        try:
            token_der = base64.b64decode(manifest.timestamp_info.token_b64)
            if manifest.manifest_hash:
                verify_timestamp(manifest.manifest_hash.encode(), token_der)
        except Exception as exc:
            warnings.append(f"Timestamp verification failed: {exc}")

    return BundleVerificationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)


async def verify_bundle_async(
    bundle_path: Path,
    public_key_pem: bytes | None = None,
) -> BundleVerificationResult:
    """Async wrapper for verify_bundle."""
    return verify_bundle(bundle_path, public_key_pem)
