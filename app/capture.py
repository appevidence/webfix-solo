# Ported from appevidence/evidence-capture-app at commit 768a60ac4951ece0f1488c4d7c23d40204013e00
from __future__ import annotations

import base64
import logging
import zipfile
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from pydantic import BaseModel

from app.config import settings
from app.hashing import hash_file_with_size
from app.manifest import build_manifest, manifest_to_json, sign_manifest
from app.metadata import build_user_agent
from app.models import ArtifactHash, ManifestV1, TimestampInfo
from app.timestamping import request_timestamp
from app.utils import ensure_dir, utcnow

log = logging.getLogger(__name__)


class CaptureOptions(BaseModel):
    url: str
    out_dir: Path
    with_pdf: bool = True
    with_har: bool = True
    with_screenshot: bool = True
    with_rfc3161: bool = False
    timeout_ms: int = 60000
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800

    model_config = {"arbitrary_types_allowed": True}


class CaptureResult(BaseModel):
    url: str
    out_dir: Path
    html_path: Path | None = None
    screenshot_path: Path | None = None
    pdf_path: Path | None = None
    har_path: Path | None = None
    artifacts: list[ArtifactHash] = []
    captured_at: datetime
    user_agent: str
    final_url: str

    model_config = {"arbitrary_types_allowed": True}


async def capture_url(options: CaptureOptions) -> CaptureResult:
    """Capture a URL using Playwright and save artifacts to out_dir."""
    ensure_dir(options.out_dir)
    captured_at = utcnow()
    user_agent = build_user_agent("chromium")
    artifacts: list[ArtifactHash] = []

    har_path: Path | None = None
    html_path: Path | None = None
    screenshot_path: Path | None = None
    pdf_path: Path | None = None
    final_url: str = options.url

    async with async_playwright() as pw:
        browser_kwargs = {
            "headless": options.headless,
        }
        browser = await pw.chromium.launch(**browser_kwargs)

        context_kwargs: dict = {
            "viewport": {
                "width": options.viewport_width,
                "height": options.viewport_height,
            },
            "user_agent": user_agent,
        }
        if options.with_har:
            har_path = options.out_dir / "capture.har"
            context_kwargs["record_har_path"] = str(har_path)

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        await page.goto(options.url, timeout=options.timeout_ms, wait_until="networkidle")
        final_url = page.url

        # Save HTML
        html_content = await page.content()
        html_path = options.out_dir / "page.html"
        html_path.write_text(html_content, encoding="utf-8")
        sha, size = hash_file_with_size(html_path)
        artifacts.append(ArtifactHash(filename="page.html", sha256=sha, size_bytes=size))

        # Save screenshot
        if options.with_screenshot:
            screenshot_path = options.out_dir / "screenshot.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            sha, size = hash_file_with_size(screenshot_path)
            artifacts.append(ArtifactHash(filename="screenshot.png", sha256=sha, size_bytes=size))

        # Save PDF
        if options.with_pdf:
            pdf_path = options.out_dir / "page.pdf"
            await page.pdf(path=str(pdf_path))
            sha, size = hash_file_with_size(pdf_path)
            artifacts.append(ArtifactHash(filename="page.pdf", sha256=sha, size_bytes=size))

        await context.close()
        await browser.close()

    # Hash HAR after context close (HAR is finalized on context close)
    if options.with_har and har_path and har_path.exists():
        sha, size = hash_file_with_size(har_path)
        artifacts.append(ArtifactHash(filename="capture.har", sha256=sha, size_bytes=size))

    return CaptureResult(
        url=options.url,
        out_dir=options.out_dir,
        html_path=html_path,
        screenshot_path=screenshot_path,
        pdf_path=pdf_path,
        har_path=har_path,
        artifacts=artifacts,
        captured_at=captured_at,
        user_agent=user_agent,
        final_url=final_url,
    )


async def run_capture(options: CaptureOptions) -> tuple[ManifestV1, Path]:
    """Full pipeline: capture + build manifest + sign + optional timestamp + write bundle zip."""
    result = await capture_url(options)
    manifest = build_manifest(
        url=result.url,
        captured_at=result.captured_at,
        user_agent=result.user_agent,
        artifacts=result.artifacts,
    )

    # Sign manifest if key exists
    key_path = settings.resolved_signing_key_path
    if key_path.exists():
        private_key_pem = key_path.read_bytes()
        manifest = sign_manifest(manifest, private_key_pem)

    # Optional RFC 3161 timestamp
    if options.with_rfc3161 and manifest.manifest_hash:
        try:
            token_der = await request_timestamp(manifest.manifest_hash.encode(), settings.tsa_url)
            manifest = manifest.model_copy(
                update={
                    "timestamp_info": TimestampInfo(
                        tsa_url=settings.tsa_url,
                        token_b64=base64.b64encode(token_der).decode(),
                        verified=True,
                    )
                }
            )
        except Exception:
            log.debug("RFC 3161 timestamping failed", exc_info=True)

    # Write manifest.json
    manifest_path = options.out_dir / "manifest.json"
    manifest_path.write_text(manifest_to_json(manifest), encoding="utf-8")

    # Create bundle zip
    bundle_name = f"bundle_{result.captured_at.strftime('%Y%m%dT%H%M%SZ')}.zip"
    bundle_path = options.out_dir / bundle_name
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "manifest.json")
        if result.html_path and result.html_path.exists():
            zf.write(result.html_path, "page.html")
        if result.screenshot_path and result.screenshot_path.exists():
            zf.write(result.screenshot_path, "screenshot.png")
        if result.pdf_path and result.pdf_path.exists():
            zf.write(result.pdf_path, "page.pdf")
        if result.har_path and result.har_path.exists():
            zf.write(result.har_path, "capture.har")

    return manifest, bundle_path
