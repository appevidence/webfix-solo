# Ported from appevidence/evidence-capture-app at commit 15cb893357d7beba5b0f40b0a61a0a8d532c3bc6
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.export import BundleContents, extract_bundle


def generate_report(bundle_contents: BundleContents, out_path: Path) -> Path:
    """Generate a PDF report from bundle contents."""
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Web Evidence Report", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    manifest = bundle_contents.manifest

    # URL
    story.append(Paragraph(f"<b>URL:</b> {manifest.url}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    # Capture time
    story.append(
        Paragraph(
            f"<b>Captured at:</b> {manifest.captured_at.isoformat()}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # User agent
    story.append(Paragraph(f"<b>User Agent:</b> {manifest.user_agent}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Artifact hashes table
    story.append(Paragraph("<b>Artifact Hashes</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.3 * cm))

    table_data = [["Filename", "SHA-256", "Size (bytes)"]]
    for artifact in manifest.artifacts:
        table_data.append(
            [
                artifact.filename,
                artifact.sha256[:16] + "...",
                str(artifact.size_bytes),
            ]
        )

    table = Table(table_data, colWidths=[4 * cm, 9 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # Verification status
    story.append(Paragraph("<b>Verification Status</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.3 * cm))

    has_signature = bool(manifest.signature_b64)
    has_timestamp = bool(manifest.timestamp_info and manifest.timestamp_info.token_b64)

    story.append(
        Paragraph(
            f"Signature: {'Present' if has_signature else 'Not present'}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"RFC 3161 Timestamp: {'Present' if has_timestamp else 'Not present'}",
            styles["Normal"],
        )
    )

    if manifest.manifest_hash:
        story.append(
            Paragraph(
                f"<b>Manifest Hash:</b> {manifest.manifest_hash}",
                styles["Normal"],
            )
        )

    doc.build(story)
    return out_path


def render_report_from_bundle(bundle_path: Path, out_path: Path) -> Path:
    """Convenience wrapper: extract bundle and generate report."""
    contents = extract_bundle(bundle_path)
    return generate_report(contents, out_path)
