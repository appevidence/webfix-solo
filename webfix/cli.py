"""``webfix`` command-line interface.

The command surface is fixed (see README.md). Implementations call into
``app.*`` modules which are being progressively ported from Repo A
(``appevidence/evidence-capture-app``); see ``docs/Current-State.md``.

While porting is in progress, sub-commands raise a ``typer.Exit(2)`` with a
clear "not yet ported" message, so the CLI shape can be exercised — and
help text rendered — without the underlying functionality being available.
"""

from __future__ import annotations

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


def _not_yet_ported(feature: str) -> typer.Exit:
    _err_console.print(
        f"[yellow]webfix:[/yellow] [bold]{feature}[/bold] is not yet ported "
        "from Repo A (appevidence/evidence-capture-app).\n"
        "See docs/Current-State.md for the port checklist.",
    )
    return typer.Exit(code=2)


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
        help="Read the Ed25519 key passphrase from stdin instead of prompting.",
    ),
) -> None:
    """Initialize the local data directory: generate Ed25519 keypair, DB, audit log."""
    target = data_dir or _default_data_dir()
    _console.print(f"webfix init -> [cyan]{target}[/cyan]")
    _ = key_password_stdin  # silence linter until ported
    raise _not_yet_ported("init")


@app.command()
def capture(
    url: str = typer.Argument(..., help="URL to capture."),
    out: Path = typer.Option(Path.cwd(), "--out", "-o", help="Directory to write the bundle into."),
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
    _ = (
        url,
        out,
        with_pdf,
        with_har,
        with_screenshot,
        with_rfc3161,
        with_ots,
        with_wayback,
        with_eth,
        timeout,
    )
    raise _not_yet_ported("capture")


@app.command()
def verify(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    """Verify signature, artifact hashes, and (if present) RFC 3161 / OTS timestamps."""
    _ = bundle
    raise _not_yet_ported("verify")


@app.command()
def export(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    to: Path = typer.Option(Path.cwd(), "--to", help="Directory to extract bundle contents into."),
) -> None:
    """Extract the contents of a bundle (HTML, screenshot, PDF, HAR, manifest, signatures)."""
    _ = (bundle, to)
    raise _not_yet_ported("export")


@app.command()
def report(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    pdf: Path = typer.Option(..., "--pdf", help="Output PDF path."),
) -> None:
    """Render a human-readable PDF report summarizing a bundle."""
    _ = (bundle, pdf)
    raise _not_yet_ported("report")


@audit_app.command("list")
def audit_list(
    data_dir: Path = typer.Option(None, "--data-dir"),
    limit: int = typer.Option(50, "--limit", min=1, max=10_000),
) -> None:
    """List recent entries from the local hash-chained audit log."""
    _ = (data_dir, limit)
    raise _not_yet_ported("audit list")


@audit_app.command("verify")
def audit_verify(
    entry_id: str = typer.Argument(..., help="Audit-log entry ID."),
    data_dir: Path = typer.Option(None, "--data-dir"),
) -> None:
    """Verify a single audit-log entry against the chain."""
    _ = (entry_id, data_dir)
    raise _not_yet_ported("audit verify")


@audit_app.command("verify-all")
def audit_verify_all(
    data_dir: Path = typer.Option(None, "--data-dir"),
) -> None:
    """Verify the entire audit-log hash chain end to end."""
    _ = data_dir
    raise _not_yet_ported("audit verify-all")


def main() -> None:
    """Console-script entry point referenced from ``pyproject.toml``."""
    try:
        app()
    except KeyboardInterrupt:  # pragma: no cover
        _err_console.print("[yellow]webfix: interrupted[/yellow]")
        sys.exit(130)


if __name__ == "__main__":  # pragma: no cover
    main()
