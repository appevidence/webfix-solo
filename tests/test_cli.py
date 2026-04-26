"""Smoke tests for the ``webfix`` CLI surface.

These do not exercise the (not-yet-ported) capture/sign/verify implementations;
they only confirm that the command tree is wired up correctly.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from webfix import __version__
from webfix.cli import app

runner = CliRunner()


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


@pytest.mark.parametrize(
    ("argv", "feature"),
    [
        (["init"], "init"),
        (["capture", "https://example.com"], "capture"),
        (["audit", "list"], "audit list"),
        (["audit", "verify-all"], "audit verify-all"),
    ],
)
def test_not_yet_ported_exits_2(argv: list[str], feature: str) -> None:
    result = runner.invoke(app, argv)
    assert result.exit_code == 2, result.output
    # The "not yet ported" marker is written to stderr.
    assert "not yet ported" in result.stderr.lower()
    assert feature in result.stderr.lower()
