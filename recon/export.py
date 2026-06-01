"""Export utilities for recon-toolkit."""

from datetime import datetime
from pathlib import Path


# ─── Triage exports ────────────────────────────────────────────────────────────

def export_triage_txt(engagement: str, results: list[dict], tier: str = "all") -> Path:
    """Export triage results to a text file. Returns the output path."""
    filtered = results if tier == "all" else [r for r in results if r["priority"] == tier]

    if tier != "all":
        # Simple host list for nuclei / ffuf
        lines = [r["host"] for r in filtered]
    else:
        lines = [r["host"] for r in filtered]

    suffix = tier if tier != "all" else "all"
    fname  = Path.home() / f"triage_{engagement}_{suffix}_{datetime.now().strftime('%Y%m%d')}.txt"
    fname.write_text("\n".join(lines))
    return fname


def export_triage_csv(
    engagement: str,
    results: list[dict],
    tier: str = "all",
    columns: list[str] | None = None,
) -> Path:
    """Export triage results to CSV with selectable columns. Returns the output path."""
    all_columns = ["priority", "status", "host", "title", "tech", "tags", "ip"]
    cols = columns if columns else all_columns

    filtered = results if tier == "all" else [r for r in results if r["priority"] == tier]

    def _row(r: dict) -> str:
        parts = []
        for c in cols:
            val = str(r.get(c) or "").replace(",", ";").replace("\n", " ")
            parts.append(val)
        return ",".join(parts)

    header = ",".join(cols)
    lines  = [header] + [_row(r) for r in filtered]

    suffix = tier if tier != "all" else "all"
    fname  = Path.home() / f"triage_{engagement}_{suffix}_{datetime.now().strftime('%Y%m%d')}.csv"
    fname.write_text("\n".join(lines))
    return fname


def export_triage_md(
    engagement: str,
    results: list[dict],
    tier: str = "all",
    columns: list[str] | None = None,
) -> Path:
    """Export triage results to a markdown table with selectable columns."""
    all_columns = ["priority", "status", "host", "title", "tech", "tags", "ip"]
    cols = columns if columns else all_columns

    col_labels = {
        "priority": "Priority",
        "status":   "Status",
        "host":     "Host",
        "title":    "Title",
        "tech":     "Tech",
        "tags":     "Tags",
        "ip":       "IP",
    }

    filtered = results if tier == "all" else [r for r in results if r["priority"] == tier]

    priority_order = {"p1": 0, "p2": 1, "p3": 2, "p4": 3}
    filtered = sorted(filtered, key=lambda r: priority_order.get(r.get("priority", "p4"), 4))

    header    = "| " + " | ".join(col_labels[c] for c in cols) + " |"
    separator = "| " + " | ".join("---" for _ in cols) + " |"

    def _row(r: dict) -> str:
        parts = []
        for c in cols:
            val = str(r.get(c) or "").replace("|", "\\|")
            if c == "priority":
                val = val.upper()
            parts.append(val[:60] if c in ("title", "tags", "tech") else val)
        return "| " + " | ".join(parts) + " |"

    tier_label = tier.upper() if tier != "all" else "All Tiers"
    lines = [
        f"# Triage Export: {engagement} — {tier_label}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total hosts: {len(filtered)}",
        "",
        header,
        separator,
    ] + [_row(r) for r in filtered]

    suffix = tier if tier != "all" else "all"
    fname  = Path.home() / f"triage_{engagement}_{suffix}_{datetime.now().strftime('%Y%m%d')}.md"
    fname.write_text("\n".join(lines))
    return fname


# ─── Findings export ───────────────────────────────────────────────────────────

def export_findings_md(engagement: str, findings: list[dict]) -> Path:
    """Export findings list to a markdown report. Returns the output path."""
    sev_order      = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Informational": 4}
    sorted_findings = sorted(findings, key=lambda r: sev_order.get(r["severity"], 5))

    lines = [
        f"# Findings Report: {engagement}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total findings: {len(findings)}",
        "",
        "## Summary",
        "",
    ]

    for sev in ("Critical", "High", "Medium", "Low", "Informational"):
        count = sum(1 for f in findings if f["severity"] == sev)
        if count:
            lines.append(f"- **{sev}**: {count}")

    lines += ["", "---", ""]

    for f in sorted_findings:
        lines += [
            f"## [{f['severity']}] {f['title']}",
            "",
            f"**Host:** {f['host']}  ",
            f"**Status:** {f['status']}  ",
            f"**Date:** {f['created_at'][:10]}",
            "",
            "### Description",
            f"{f['description']}",
            "",
            "### Evidence",
            f"{f['evidence']}",
            "",
            "### Impact",
            f"{f['impact']}",
            "",
            "### Recommendation",
            f"{f['recommendation']}",
            "",
            "---",
            "",
        ]

    fname = Path.home() / f"findings_{engagement}_{datetime.now().strftime('%Y%m%d')}.md"
    fname.write_text("\n".join(lines))
    return fname
