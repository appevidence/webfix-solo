"""``webfix`` command-line interface.

Each sub-command is wired to one or more modules under ``app.*`` (ported from
``appevidence/evidence-capture-app`` — "Repo A" — with the web layer removed):

* ``webfix init``    → :mod:`app.signing` + :mod:`app.database` + :mod:`app.audit`
* ``webfix capture`` → :mod:`app.capture` (+ :mod:`app.audit`, :mod:`app.database`)
* ``webfix verify``  → :mod:`app.verify`
* ``webfix export``  → :mod:`app.export`
* ``webfix report``  → :mod:`app.report`
* ``webfix audit …`` → :mod:`app.audit_admin`

Status of each ported module is tracked in ``docs/Current-State.md``.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

from webfix import __version__

app = typer.Typer(
    name="webfix",
    help="Minimalist single-user CLI for hash-chained, signed web-page captures.",
    no_args_is_help=True,
    add_completion=False,
)
audit_app = typer.Typer(
    name="audit",
    help="Inspect and verify the local hash-chained audit log.",
    no_args_is_help=True,
)
app.add_typer(audit_app, name="audit")

_console = Console()
_err_console = Console(stderr=True)

_KEYS_SUBDIR = "keys"
_PRIVATE_KEY_NAME = "signing.key"
_PUBLIC_KEY_NAME = "signing.pub"
_BUNDLES_SUBDIR = "bundles"
_AUDIT_LOG_NAME = "audit.log"
_DB_NAME = "db.sqlite"


def _default_data_dir() -> Path:
    """Return the default per-user data directory.

    Honors ``$WEBFIX_DATA_DIR`` and ``$XDG_DATA_HOME`` before falling back to
    ``~/.local/share/webfix-solo``.
    """
    override = os.environ.get("WEBFIX_DATA_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "webfix-solo"


def _resolve_data_dir(data_dir: Path | None) -> Path:
    """Resolve the effective data directory and sync :mod:`app.config`.

    The ``app.config.settings`` singleton is updated so that downstream modules
    (capture, audit, etc.) that consult it see the same path the CLI is using.
    """
    target = (data_dir or _default_data_dir()).expanduser().resolve()
    # Sync the global settings singleton so downstream modules see the same dir.
    from app.config import settings as _settings

    _settings.data_dir = target
    return target


def _abort(msg: str, code: int = 1) -> typer.Exit:
    _err_console.print(f"[red]webfix:[/red] {msg}")
    return typer.Exit(code=code)


def _read_passphrase_from_stdin() -> bytes | None:
    """Read a passphrase from stdin (one line). Empty input means no passphrase."""
    raw = sys.stdin.readline()
    pw = raw.rstrip("\n").rstrip("\r")
    return pw.encode() if pw else None


def _version_callback(value: bool) -> None:
    if value:
        _console.print(f"webfix {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Top-level options for ``webfix``."""


# --------------------------------------------------------------------------- #
# init
# --------------------------------------------------------------------------- #
@app.command()
def init(
    data_dir: Path = typer.Option(
        None,
        "--data-dir",
        help="Where to create keys/, db.sqlite, audit.log, bundles/. "
        "Defaults to $WEBFIX_DATA_DIR or $XDG_DATA_HOME/webfix-solo.",
    ),
    key_password_stdin: bool = typer.Option(
        False,
        "--key-password-stdin",
        help="Read the Ed25519 key passphrase from stdin instead of leaving the key unencrypted.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite an existing signing key (DESTROYS the previous key!).",
    ),
) -> None:
    """Initialize the local data directory: generate Ed25519 keypair, DB, audit log."""
    from app.audit import AuditLog
    from app.database import init_db
    from app.signing import generate_keypair

    target = _resolve_data_dir(data_dir)
    keys_dir = target / _KEYS_SUBDIR
    bundles_dir = target / _BUNDLES_SUBDIR
    private_path = keys_dir / _PRIVATE_KEY_NAME
    public_path = keys_dir / _PUBLIC_KEY_NAME
    db_path = target / _DB_NAME
    audit_log_path = target / _AUDIT_LOG_NAME

    _console.print(f"webfix init -> [cyan]{target}[/cyan]")

    target.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)
    bundles_dir.mkdir(parents=True, exist_ok=True)

    if private_path.exists() and not force:
        raise _abort(
            f"signing key already exists at {private_path}; "
            "refusing to overwrite (use --force to replace it)."
        )

    passphrase: bytes | None = None
    if key_password_stdin:
        passphrase = _read_passphrase_from_stdin()
        if passphrase is None:
            raise _abort("--key-password-stdin was given but stdin was empty.")

    private_pem, public_pem = generate_keypair(passphrase=passphrase)
    private_path.write_bytes(private_pem)
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        # Best-effort: not all filesystems support chmod (e.g. on Windows).
        pass
    public_path.write_bytes(public_pem)

    init_db(db_path)

    log = AuditLog(audit_log_path)
    log.append(action="init")

    _console.print("  [green]✓[/green] keypair generated:    " f"[dim]{private_path}[/dim]")
    _console.print("  [green]✓[/green] public key written:   " f"[dim]{public_path}[/dim]")
    _console.print("  [green]✓[/green] sqlite db initialised:" f" [dim]{db_path}[/dim]")
    _console.print("  [green]✓[/green] audit log seeded:     " f"[dim]{audit_log_path}[/dim]")


# --------------------------------------------------------------------------- #
# capture
# --------------------------------------------------------------------------- #
@app.command()
def capture(
    url: str = typer.Argument(..., help="URL to capture."),
    out: Path = typer.Option(
        None,
        "--out",
        "-o",
        help="Directory to write the bundle into. Defaults to <data-dir>/bundles.",
    ),
    data_dir: Path = typer.Option(None, "--data-dir"),
    with_pdf: bool = typer.Option(True, "--with-pdf/--no-pdf", help="Emit a PDF rendering."),
    with_har: bool = typer.Option(True, "--with-har/--no-har", help="Emit a HAR file."),
    with_screenshot: bool = typer.Option(
        True, "--with-screenshot/--no-screenshot", help="Emit a full-page screenshot."
    ),
    with_rfc3161: bool = typer.Option(
        False, "--with-rfc3161", help="Request an RFC 3161 timestamp for the manifest."
    ),
    with_ots: bool = typer.Option(
        False, "--with-ots", help="Request an OpenTimestamps proof (requires [ots] extra)."
    ),
    with_wayback: bool = typer.Option(
        False, "--with-wayback", help="Submit the URL to the Wayback Machine."
    ),
    with_eth: bool = typer.Option(
        False, "--with-eth", help="Anchor the manifest hash on Ethereum (requires [eth] extra)."
    ),
    timeout: int = typer.Option(60, "--timeout", min=1, help="Per-page timeout in seconds."),
) -> None:
    """Capture a single URL and emit a signed evidence bundle (.zip)."""
    from app.audit import AuditLog
    from app.capture import CaptureOptions, run_capture
    from app.url_redaction import redact_url_for_log

    target = _resolve_data_dir(data_dir)
    out_dir = (out or (target / _BUNDLES_SUBDIR)).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for flag_name, flag_value in (
        ("--with-ots", with_ots),
        ("--with-wayback", with_wayback),
        ("--with-eth", with_eth),
    ):
        if flag_value:
            _err_console.print(
                f"[yellow]webfix:[/yellow] {flag_name} is not yet implemented "
                "(see docs/Current-State.md → Optional extras); proceeding without it."
            )

    options = CaptureOptions(
        url=url,
        out_dir=out_dir,
        with_pdf=with_pdf,
        with_har=with_har,
        with_screenshot=with_screenshot,
        with_rfc3161=with_rfc3161,
        timeout_ms=timeout * 1000,
    )

    _console.print(f"webfix capture [cyan]{redact_url_for_log(url)}[/cyan] -> [dim]{out_dir}[/dim]")

    try:
        manifest, bundle_path = asyncio.run(run_capture(options))
    except Exception as exc:
        raise _abort(f"capture failed: {exc}") from exc

    audit_log_path = target / _AUDIT_LOG_NAME
    log = AuditLog(audit_log_path)
    log.append(
        action="capture",
        url=redact_url_for_log(url),
        bundle_hash=manifest.manifest_hash,
    )

    _console.print(f"  [green]✓[/green] bundle: [bold]{bundle_path}[/bold]")
    if manifest.manifest_hash:
        _console.print(f"  [green]✓[/green] manifest hash: [dim]{manifest.manifest_hash}[/dim]")
    if manifest.signature_b64:
        _console.print("  [green]✓[/green] signed with local key")
    if manifest.timestamp_info and manifest.timestamp_info.token_b64:
        _console.print(f"  [green]✓[/green] RFC 3161 timestamp: {manifest.timestamp_info.tsa_url}")


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
@app.command()
def verify(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    public_key: Path = typer.Option(
        None,
        "--public-key",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Public key PEM to verify with. Defaults to the key embedded in the manifest.",
    ),
) -> None:
    """Verify signature, artifact hashes, and (if present) RFC 3161 / OTS timestamps."""
    from app.verify import verify_bundle

    pub_pem = public_key.read_bytes() if public_key else None
    result = verify_bundle(bundle, public_key_pem=pub_pem)

    if result.ok:
        _console.print(f"[green]webfix verify:[/green] [bold]OK[/bold]  {bundle}")
        for warning in result.warnings:
            _err_console.print(f"  [yellow]warning:[/yellow] {warning}")
        return

    _err_console.print(f"[red]webfix verify:[/red] [bold]FAIL[/bold]  {bundle}")
    for err in result.errors:
        _err_console.print(f"  [red]✗[/red] {err}")
    for warning in result.warnings:
        _err_console.print(f"  [yellow]warning:[/yellow] {warning}")
    raise typer.Exit(code=1)


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
@app.command()
def export(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    to: Path = typer.Option(Path.cwd(), "--to", help="Directory to extract bundle contents into."),
) -> None:
    """Extract the contents of a bundle (HTML, screenshot, PDF, HAR, manifest, signatures)."""
    from app.export import export_bundle

    try:
        extracted = export_bundle(bundle, to)
    except Exception as exc:
        raise _abort(f"export failed: {exc}") from exc

    _console.print(f"webfix export [cyan]{bundle}[/cyan] -> [dim]{to}[/dim]")
    for path in extracted:
        _console.print(f"  [green]✓[/green] {path}")


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
@app.command()
def report(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    pdf: Path = typer.Option(..., "--pdf", help="Output PDF path."),
) -> None:
    """Render a human-readable PDF report summarizing a bundle."""
    from app.report import render_report_from_bundle

    try:
        out_path = render_report_from_bundle(bundle, pdf)
    except Exception as exc:
        raise _abort(f"report generation failed: {exc}") from exc

    _console.print(f"[green]webfix report:[/green] wrote [bold]{out_path}[/bold]")


# --------------------------------------------------------------------------- #
# audit
# --------------------------------------------------------------------------- #
@audit_app.command("list")
def audit_list(
    data_dir: Path = typer.Option(None, "--data-dir"),
    limit: int = typer.Option(50, "--limit", min=1, max=10_000),
) -> None:
    """List recent entries from the local hash-chained audit log."""
    from app.audit_admin import list_audit_entries

    target = _resolve_data_dir(data_dir)
    entries = list_audit_entries(target, limit=limit)
    if not entries:
        _console.print("[dim]no audit entries[/dim]")
        return
    for entry in entries:
        url_part = f"  url={entry.url}" if entry.url else ""
        bundle_part = f"  bundle={entry.bundle_hash[:12]}…" if entry.bundle_hash else ""
        _console.print(
            f"[dim]{entry.timestamp.isoformat()}[/dim]  "
            f"[cyan]{entry.action:<8}[/cyan]  "
            f"id={entry.entry_id}{url_part}{bundle_part}"
        )


@audit_app.command("verify")
def audit_verify(
    entry_id: str = typer.Argument(..., help="Audit-log entry ID."),
    data_dir: Path = typer.Option(None, "--data-dir"),
) -> None:
    """Verify a single audit-log entry against the chain."""
    from app.audit_admin import verify_audit_entry

    target = _resolve_data_dir(data_dir)
    ok, message = verify_audit_entry(target, entry_id)
    if ok:
        _console.print(f"[green]webfix audit verify:[/green] {message}")
        return
    _err_console.print(f"[red]webfix audit verify:[/red] {message}")
    raise typer.Exit(code=1)


@audit_app.command("verify-all")
def audit_verify_all(
    data_dir: Path = typer.Option(None, "--data-dir"),
) -> None:
    """Verify the entire audit-log hash chain end to end."""
    from app.audit_admin import verify_audit_chain

    target = _resolve_data_dir(data_dir)
    ok, errors = verify_audit_chain(target)
    if ok:
        _console.print("[green]webfix audit verify-all:[/green] [bold]chain OK[/bold]")
        return
    _err_console.print("[red]webfix audit verify-all:[/red] [bold]chain BROKEN[/bold]")
    for err in errors:
        _err_console.print(f"  [red]✗[/red] {err}")
    raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point referenced from ``pyproject.toml``."""
    try:
        app()
    except KeyboardInterrupt:  # pragma: no cover
        _err_console.print("[yellow]webfix: interrupted[/yellow]")
        sys.exit(130)


if __name__ == "__main__":  # pragma: no cover
    main()
