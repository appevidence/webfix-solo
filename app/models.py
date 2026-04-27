# Ported from appevidence/evidence-capture-app at commit 72516054ed6711c426c76ca784b9addccd688c0f
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ArtifactHash(BaseModel):
    filename: str
    sha256: str
    size_bytes: int


class TimestampInfo(BaseModel):
    tsa_url: str | None = None
    token_b64: str | None = None
    verified: bool = False


class ManifestV1(BaseModel):
    version: Literal["1"] = "1"
    url: str
    captured_at: datetime
    user_agent: str
    artifacts: list[ArtifactHash]
    manifest_hash: str | None = None
    signature_b64: str | None = None
    public_key_b64: str | None = None
    timestamp_info: TimestampInfo | None = None


class BundleVerificationResult(BaseModel):
    ok: bool
    errors: list[str] = []
    warnings: list[str] = []
