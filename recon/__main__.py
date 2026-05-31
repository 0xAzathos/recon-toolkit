"""Entry point for recon-toolkit. Run as `recon` or `python -m recon`."""

import argparse
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from recon import __version__
from recon import db
from recon.export import export_findings_md

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="recon",
        description="recon-toolkit — Personal VDP and bug bounty recon toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  recon                                 Launch TUI
  recon --engagement uscourts-2026      Launch with engagement preselected
  recon --list-engagements              List all engagements (no TUI)
  recon --export-findings NAME          Export findings to markdown (no TUI)
  recon --version                       Show version and exit
        """,
    )
    parser.add_argument(
        "--engagement", "-e",
        metavar="NAME",
        help="Start with this engagement active",
    )
    parser.add_argument(
        "--list-engagements",
        action="store_true",
        help="List all engagements and exit",
    )
    parser.add_argument(
        "--export-findings",
        metavar="NAME",
        help="Export findings for an engagement to markdown and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"recon-toolkit {__version__}",
    )
    args = parser.parse_args()

    db.init_db()

    if args.list_engagements:
        engagements = db.list_engagements()
        if not engagements:
            console.print("[yellow]No engagements found. Create one in the TUI.[/]")
            return
        t = Table("Name", "Scope", "Created", box=box.SIMPLE, style="cyan")
        for e in engagements:
            t.add_row(e["name"], e["scope"] or "—", e["created_at"][:10])
        console.print(t)
        return

    if args.export_findings:
        findings = db.list_findings(args.export_findings)
        if not findings:
            console.print(
                f"[yellow]No findings for engagement: {args.export_findings}[/]"
            )
            return
        path = export_findings_md(args.export_findings, findings)
        console.print(f"[green]Exported {len(findings)} findings to {path}[/]")
        return

    from recon.ui.app import ReconApp
    app = ReconApp(start_engagement=args.engagement)
    app.run()


if __name__ == "__main__":
    main()
