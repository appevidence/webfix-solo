# Ported from appevidence/evidence-capture-app at commit d6c1fb2d8cadb36607031916e2f577a416dfd420
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

log = logging.getLogger(__name__)


class AuditEntry(BaseModel):
    entry_id: str
    timestamp: datetime
    action: str
    url: str | None = None
    bundle_hash: str | None = None
    prev_hash: str | None = None
    entry_hash: str


def _compute_entry_hash(
    entry_id: str,
    timestamp: datetime,
    action: str,
    url: str | None,
    bundle_hash: str | None,
    prev_hash: str | None,
) -> str:
    """Compute SHA-256 hash for an audit entry."""
    parts = [
        prev_hash or "",
        entry_id,
        timestamp.isoformat(),
        action,
        url or "",
        bundle_hash or "",
    ]
    content = "|".join(parts).encode()
    return hashlib.sha256(content).hexdigest()


class AuditLog:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_last_hash(self) -> str | None:
        """Return the entry_hash of the most recent entry, or None."""
        last: str | None = None
        if self._log_path.exists():
            with self._log_path.open() as fh:
                for raw_line in fh:
                    stripped = raw_line.strip()
                    if stripped:
                        try:
                            data = json.loads(stripped)
                            last = data.get("entry_hash")
                        except json.JSONDecodeError:
                            pass
        return last

    def append(
        self,
        action: str,
        url: str | None = None,
        bundle_hash: str | None = None,
    ) -> AuditEntry:
        """Append a new entry to the audit log."""
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)
        prev_hash = self._get_last_hash()
        entry_hash = _compute_entry_hash(entry_id, timestamp, action, url, bundle_hash, prev_hash)
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            action=action,
            url=url,
            bundle_hash=bundle_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        with self._log_path.open("a") as fh:
            fh.write(entry.model_dump_json() + "\n")
        return entry

    def get_entries(self, limit: int = 50) -> list[AuditEntry]:
        """Return the most recent `limit` entries."""
        if not self._log_path.exists():
            return []
        entries: list[AuditEntry] = []
        with self._log_path.open() as fh:
            for raw_line in fh:
                stripped = raw_line.strip()
                if stripped:
                    try:
                        entries.append(AuditEntry.model_validate_json(stripped))
                    except Exception:
                        log.debug("Failed to parse audit entry", exc_info=True)
        return entries[-limit:]

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the entire hash chain. Returns (ok, errors)."""
        if not self._log_path.exists():
            return True, []
        entries: list[AuditEntry] = []
        with self._log_path.open() as fh:
            for raw_line in fh:
                stripped = raw_line.strip()
                if stripped:
                    try:
                        entries.append(AuditEntry.model_validate_json(stripped))
                    except Exception as exc:
                        return False, [f"Failed to parse entry: {exc}"]

        errors: list[str] = []
        for i, entry in enumerate(entries):
            expected_prev = entries[i - 1].entry_hash if i > 0 else None
            if entry.prev_hash != expected_prev:
                errors.append(
                    f"Entry {entry.entry_id}: prev_hash mismatch "
                    f"(expected {expected_prev!r}, got {entry.prev_hash!r})"
                )
            expected_hash = _compute_entry_hash(
                entry.entry_id,
                entry.timestamp,
                entry.action,
                entry.url,
                entry.bundle_hash,
                entry.prev_hash,
            )
            if entry.entry_hash != expected_hash:
                errors.append(
                    f"Entry {entry.entry_id}: entry_hash mismatch "
                    f"(expected {expected_hash!r}, got {entry.entry_hash!r})"
                )
        return len(errors) == 0, errors

    def verify_entry(self, entry_id: str) -> tuple[bool, str]:
        """Verify a single entry by ID. Returns (ok, message)."""
        if not self._log_path.exists():
            return False, f"Entry {entry_id!r} not found (log does not exist)"

        entries: list[AuditEntry] = []
        with self._log_path.open() as fh:
            for raw_line in fh:
                stripped = raw_line.strip()
                if stripped:
                    try:
                        entries.append(AuditEntry.model_validate_json(stripped))
                    except Exception:
                        log.debug("Failed to parse audit entry", exc_info=True)

        for i, entry in enumerate(entries):
            if entry.entry_id != entry_id:
                continue
            expected_hash = _compute_entry_hash(
                entry.entry_id,
                entry.timestamp,
                entry.action,
                entry.url,
                entry.bundle_hash,
                entry.prev_hash,
            )
            if entry.entry_hash != expected_hash:
                return False, f"Entry {entry_id!r}: hash mismatch"
            expected_prev = entries[i - 1].entry_hash if i > 0 else None
            if entry.prev_hash != expected_prev:
                return False, f"Entry {entry_id!r}: prev_hash mismatch"
            return True, f"Entry {entry_id!r} is valid"
        return False, f"Entry {entry_id!r} not found"
