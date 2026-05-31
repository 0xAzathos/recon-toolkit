"""Export utilities for recon-toolkit."""

from datetime import datetime
from pathlib import Path


def export_findings_md(engagement: str, findings: list[dict]) -> Path:
    """Export findings list to a markdown report. Returns the output path."""
    sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Informational": 4}
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


def export_triage_txt(engagement: str, results: list[dict], tier: str = "all") -> Path:
    """Export triage results to a text file. Returns the output path."""
    filtered = results if tier == "all" else [r for r in results if r["priority"] == tier]
    lines = []
    if tier == "all":
        for r in filtered:
            lines.append(
                f"{r['priority'].upper()}\t[{r['status']}]\t{r['host']}\t"
                f"{r.get('tags','')}\t{r.get('title','')}"
            )
    else:
        lines = [r["host"] for r in filtered]

    suffix = tier if tier != "all" else "all"
    fname  = Path.home() / f"triage_{engagement}_{suffix}_{datetime.now().strftime('%Y%m%d')}.txt"
    fname.write_text("\n".join(lines))
    return fname
