"""End-to-end tests for the ``webfix`` CLI surface.

Exercises every command that does not require a real browser. The ``capture``
command is exercised via a fake :func:`app.capture.run_capture` so we cover the
CLI plumbing (argument parsing, audit-log append, error path) without driving
Playwright.
"""

from __future__ import annotations

import hashlib
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from app.audit import AuditLog
from app.manifest import build_manifest, manifest_to_json, sign_manifest
from app.models import ArtifactHash
from app.signing import generate_keypair
from webfix import __version__
from webfix.cli import app

runner = CliRunner()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _make_signed_bundle(tmp_path: Path) -> tuple[Path, bytes]:
    """Create a signed bundle.zip in *tmp_path*; return (bundle_path, public_pem)."""
    html = b"<html><body>hello</body></html>"
    artifacts = [
        ArtifactHash(
            filename="page.html",
            sha256=hashlib.sha256(html).hexdigest(),
            size_bytes=len(html),
        )
    ]
    manifest = build_manifest(
        url="https://example.com",
        captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        user_agent="test/1.0",
        artifacts=artifacts,
    )
    priv_pem, pub_pem = generate_keypair()
    manifest = sign_manifest(manifest, priv_pem)

    bundle = tmp_path / "bundle.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_to_json(manifest))
        zf.writestr("page.html", html)
    return bundle, pub_pem


# --------------------------------------------------------------------------- #
# top-level
# --------------------------------------------------------------------------- #


def test_help_renders() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert "webfix" in result.output.lower()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert __version__ in result.output


@pytest.mark.parametrize(
    "argv",
    [
        ["init", "--help"],
        ["capture", "--help"],
        ["verify", "--help"],
        ["export", "--help"],
        ["report", "--help"],
        ["audit", "--help"],
        ["audit", "list", "--help"],
        ["audit", "verify", "--help"],
        ["audit", "verify-all", "--help"],
    ],
)
def test_subcommand_help(argv: list[str]) -> None:
    result = runner.invoke(app, argv)
    assert result.exit_code == 0, result.output


# --------------------------------------------------------------------------- #
# init
# --------------------------------------------------------------------------- #


def test_init_creates_layout(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    result = runner.invoke(app, ["init", "--data-dir", str(data_dir)])
    assert result.exit_code == 0, result.stderr or result.output
    assert (data_dir / "keys" / "signing.key").exists()
    assert (data_dir / "keys" / "signing.pub").exists()
    assert (data_dir / "bundles").is_dir()
    assert (data_dir / "db.sqlite").exists()
    assert (data_dir / "audit.log").exists()
    # The first audit entry records the init action.
    entries = AuditLog(data_dir / "audit.log").get_entries()
    assert len(entries) == 1
    assert entries[0].action == "init"


def test_init_refuses_to_overwrite(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    runner.invoke(app, ["init", "--data-dir", str(data_dir)])
    result = runner.invoke(app, ["init", "--data-dir", str(data_dir)])
    assert result.exit_code != 0
    assert "already exists" in (result.stderr or result.output).lower()


def test_init_force_overwrites_key(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    runner.invoke(app, ["init", "--data-dir", str(data_dir)])
    first_key = (data_dir / "keys" / "signing.key").read_bytes()
    result = runner.invoke(app, ["init", "--data-dir", str(data_dir), "--force"])
    assert result.exit_code == 0, result.stderr or result.output
    assert (data_dir / "keys" / "signing.key").read_bytes() != first_key


def test_init_with_password_stdin(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    result = runner.invoke(
        app,
        ["init", "--data-dir", str(data_dir), "--key-password-stdin"],
        input="hunter2\n",
    )
    assert result.exit_code == 0, result.stderr or result.output
    pem = (data_dir / "keys" / "signing.key").read_bytes()
    # An encrypted PKCS8 key has a distinct PEM header.
    assert b"ENCRYPTED PRIVATE KEY" in pem


def test_init_password_stdin_empty(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    result = runner.invoke(
        app,
        ["init", "--data-dir", str(data_dir), "--key-password-stdin"],
        input="",
    )
    assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #


def test_verify_valid_bundle(tmp_path: Path) -> None:
    bundle, _ = _make_signed_bundle(tmp_path)
    result = runner.invoke(app, ["verify", str(bundle)])
    assert result.exit_code == 0, result.stderr or result.output
    assert "ok" in result.output.lower()


def test_verify_with_external_public_key(tmp_path: Path) -> None:
    bundle, pub_pem = _make_signed_bundle(tmp_path)
    pub_path = tmp_path / "signing.pub"
    pub_path.write_bytes(pub_pem)
    result = runner.invoke(app, ["verify", str(bundle), "--public-key", str(pub_path)])
    assert result.exit_code == 0, result.stderr or result.output


def test_verify_tampered_bundle_exits_1(tmp_path: Path) -> None:
    bundle, _ = _make_signed_bundle(tmp_path)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle, "r") as src, zipfile.ZipFile(tampered, "w") as dst:
        for name in src.namelist():
            payload = b"<html>TAMPERED</html>" if name == "page.html" else src.read(name)
            dst.writestr(name, payload)
    result = runner.invoke(app, ["verify", str(tampered)])
    assert result.exit_code == 1
    assert "fail" in (result.stderr or "").lower()


def test_verify_missing_bundle_typer_error() -> None:
    result = runner.invoke(app, ["verify", "/nonexistent/bundle.zip"])
    # Typer's `exists=True` Argument validation rejects with exit code 2.
    assert result.exit_code == 2


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #


def test_export_extracts_files(tmp_path: Path) -> None:
    bundle, _ = _make_signed_bundle(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["export", str(bundle), "--to", str(out)])
    assert result.exit_code == 0, result.stderr or result.output
    assert (out / "manifest.json").exists()
    assert (out / "page.html").exists()


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #


def test_report_generates_pdf(tmp_path: Path) -> None:
    bundle, _ = _make_signed_bundle(tmp_path)
    pdf = tmp_path / "report.pdf"
    result = runner.invoke(app, ["report", str(bundle), "--pdf", str(pdf)])
    assert result.exit_code == 0, result.stderr or result.output
    assert pdf.exists() and pdf.stat().st_size > 0
    assert pdf.read_bytes().startswith(b"%PDF")


# --------------------------------------------------------------------------- #
# audit
# --------------------------------------------------------------------------- #


def _seed_audit(data_dir: Path) -> list[str]:
    data_dir.mkdir(parents=True, exist_ok=True)
    log = AuditLog(data_dir / "audit.log")
    a = log.append(action="init")
    b = log.append(action="capture", url="https://example.com", bundle_hash="deadbeef" * 8)
    c = log.append(action="verify", url="https://example.com")
    return [a.entry_id, b.entry_id, c.entry_id]


def test_audit_list(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ids = _seed_audit(data_dir)
    result = runner.invoke(app, ["audit", "list", "--data-dir", str(data_dir)])
    assert result.exit_code == 0, result.stderr or result.output
    for entry_id in ids:
        assert entry_id in result.output


def test_audit_list_empty(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    result = runner.invoke(app, ["audit", "list", "--data-dir", str(data_dir)])
    assert result.exit_code == 0
    assert "no audit entries" in result.output.lower()


def test_audit_verify_single(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ids = _seed_audit(data_dir)
    result = runner.invoke(
        app, ["audit", "verify", ids[1], "--data-dir", str(data_dir)]
    )
    assert result.exit_code == 0, result.stderr or result.output
    assert "valid" in result.output.lower()


def test_audit_verify_unknown_id(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _seed_audit(data_dir)
    missing = "00000000-0000-0000-0000-000000000000"
    result = runner.invoke(
        app, ["audit", "verify", missing, "--data-dir", str(data_dir)]
    )
    assert result.exit_code == 1
    assert "not found" in (result.stderr or "").lower()


def test_audit_verify_all_ok(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _seed_audit(data_dir)
    result = runner.invoke(app, ["audit", "verify-all", "--data-dir", str(data_dir)])
    assert result.exit_code == 0, result.stderr or result.output
    assert "ok" in result.output.lower()


def test_audit_verify_all_detects_tamper(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _seed_audit(data_dir)
    log_path = data_dir / "audit.log"
    lines = log_path.read_text().splitlines()
    # Tamper with the URL inside the second entry without recomputing hash.
    lines[1] = lines[1].replace("example.com", "evil.com")
    log_path.write_text("\n".join(lines) + "\n")

    result = runner.invoke(app, ["audit", "verify-all", "--data-dir", str(data_dir)])
    assert result.exit_code == 1
    assert "broken" in (result.stderr or "").lower()


# --------------------------------------------------------------------------- #
# capture (pipeline mocked — no Playwright)
# --------------------------------------------------------------------------- #


def test_capture_writes_bundle_and_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: capture command writes the bundle returned by run_capture
    and appends an audit entry with the redacted URL + manifest hash."""
    data_dir = tmp_path / "data"
    runner.invoke(app, ["init", "--data-dir", str(data_dir)])

    captured_args: dict = {}

    async def fake_run_capture(options):
        captured_args["options"] = options
        # Build a fake manifest+bundle in the requested out_dir.
        html = b"<html>x</html>"
        artifacts = [
            ArtifactHash(
                filename="page.html",
                sha256=hashlib.sha256(html).hexdigest(),
                size_bytes=len(html),
            )
        ]
        manifest = build_manifest(
            url=options.url,
            captured_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            user_agent="test/1.0",
            artifacts=artifacts,
        )
        priv_pem, _ = generate_keypair()
        manifest = sign_manifest(manifest, priv_pem)
        bundle = options.out_dir / "bundle_test.zip"
        options.out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(bundle, "w") as zf:
            zf.writestr("manifest.json", manifest_to_json(manifest))
            zf.writestr("page.html", html)
        return manifest, bundle

    # Patch the symbol the CLI will import lazily.
    import app.capture as app_capture

    monkeypatch.setattr(app_capture, "run_capture", fake_run_capture)

    result = runner.invoke(
        app,
        [
            "capture",
            "https://example.com/?token=secret",
            "--data-dir",
            str(data_dir),
            "--no-pdf",
            "--no-har",
            "--no-screenshot",
        ],
    )
    assert result.exit_code == 0, result.stderr or result.output

    # Bundle was written under <data-dir>/bundles by default.
    bundles = list((data_dir / "bundles").glob("*.zip"))
    assert len(bundles) == 1

    # Audit log: init + capture; URL is redacted (token=[REDACTED]).
    entries = AuditLog(data_dir / "audit.log").get_entries()
    assert [e.action for e in entries] == ["init", "capture"]
    assert "secret" not in (entries[1].url or "")
    assert "REDACTED" in (entries[1].url or "")

    # CaptureOptions plumbing: timeout in ms, flags propagated.
    opts = captured_args["options"]
    assert opts.url == "https://example.com/?token=secret"
    assert opts.with_pdf is False
    assert opts.with_har is False
    assert opts.with_screenshot is False
    assert opts.timeout_ms == 60_000


def test_capture_warns_on_unported_extras(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    runner.invoke(app, ["init", "--data-dir", str(data_dir)])

    async def fake_run_capture(options):
        bundle = options.out_dir / "bundle.zip"
        options.out_dir.mkdir(parents=True, exist_ok=True)
        artifacts = [ArtifactHash(filename="x", sha256="0" * 64, size_bytes=0)]
        manifest = build_manifest(
            url=options.url,
            captured_at=datetime(2024, 1, 1, tzinfo=UTC),
            user_agent="t",
            artifacts=artifacts,
        )
        with zipfile.ZipFile(bundle, "w") as zf:
            zf.writestr("manifest.json", manifest_to_json(manifest))
        return manifest, bundle

    import app.capture as app_capture

    monkeypatch.setattr(app_capture, "run_capture", fake_run_capture)

    result = runner.invoke(
        app,
        [
            "capture",
            "https://example.com",
            "--data-dir",
            str(data_dir),
            "--with-ots",
            "--with-wayback",
            "--with-eth",
        ],
    )
    assert result.exit_code == 0, result.stderr or result.output
    stderr = result.stderr or ""
    assert "--with-ots" in stderr
    assert "--with-wayback" in stderr
    assert "--with-eth" in stderr


def test_capture_propagates_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data"
    runner.invoke(app, ["init", "--data-dir", str(data_dir)])

    async def boom(options):
        del options
        raise RuntimeError("playwright crashed")

    import app.capture as app_capture

    monkeypatch.setattr(app_capture, "run_capture", boom)

    result = runner.invoke(
        app, ["capture", "https://example.com", "--data-dir", str(data_dir)]
    )
    assert result.exit_code == 1
    assert "capture failed" in (result.stderr or "").lower()
