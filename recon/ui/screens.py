"""Modal screens for recon-toolkit TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Markdown, Select, TextArea

from recon import __version__
from recon.triage import PRIORITY_CRITERIA, PRIORITY_LABELS

HELP_TEXT = f"""
# recon-toolkit v{__version__} — Help

## Navigation
Switch modules using the **tab bar** at the top.
Press **?** at any time to open this screen.
Press **q** or **Ctrl+C** to quit.

---

## Engagements
Everything in recon-toolkit is scoped to an **engagement** — one per program or target.
All findings, notes, triage results, and scope are stored separately per engagement.

Create a new engagement with **+ New** in the sidebar.
Click any engagement name to switch to it.

Data is stored locally at `~/.recon_toolkit.db`. Nothing leaves your machine.

---

## Triage
Paste **httpx output** into the text area and press **Run Triage**.

Each line should look like:
```
https://admin.example.gov [200] [Admin Panel] [Apache] [1.2.3.4]
```

Priority tiers:

| Tier | Label | Criteria |
|------|-------|----------|
| P1 | CRITICAL | Admin panels, server errors (5xx) |
| P2 | HIGH | Dev/staging/test environments, APIs, known frameworks |
| P3 | MEDIUM | Auth walls (401), forbidden (403), non-HTTP services |
| P4 | LOW | Standard web with no notable signals |

Use the filter buttons to view by tier.
**Export P1** and **Export P2** save host lists ready to feed into nuclei or ffuf.
**Export All** saves a full TSV with priority, status, tags, and title.

Results are saved to the active engagement database.

---

## Findings
Structured vulnerability log for everything you discover.

**Fields:**
- **Title** — Short descriptive name of the finding
- **Host** — Affected hostname or URL
- **Severity** — Critical / High / Medium / Low / Informational
- **Description** — What the issue is and how it works
- **Evidence** — HTTP requests, responses, screenshots references
- **Impact** — Realistic attack path and worst-case outcome
- **Recommendation** — Concrete remediation steps
- **Status** — Open / Triaged / Resolved / Informational

**Export MD** generates a formatted markdown findings report sorted by severity.

---

## Headers
Paste raw HTTP response headers to score the security posture of a target.

Checks performed:
- Missing security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.)
- CSP in report-only mode rather than enforced
- Cookie flag issues (HttpOnly, Secure, SameSite)
- Server and technology version disclosure headers
- Weak or misconfigured header values

A score out of **100** is calculated. Deductions per issue:
- High severity: -20 pts
- Medium severity: -10 pts
- Low severity: -5 pts

---

## Notes
Freeform notes scoped to the active engagement.
Optionally tag each note to a specific host for easy filtering later.
All notes are timestamped automatically.

---

## Scope
Define the in-scope domains and IP ranges for the active engagement.
One entry per line. Wildcards supported:

```
*.example.gov
sub.example.gov
192.168.1.0/24
```

Use the **Check** button to instantly verify whether a host is in scope
before you probe it.

---

## CLI Mode (no TUI)
```bash
recon --list-engagements
recon --engagement NAME
recon --export-findings NAME
recon --version
```

---

## Shortcuts
| Key | Action |
|-----|--------|
| `?` | This help screen |
| `q` | Quit |
| `Tab` | Next tab |
| `Shift+Tab` | Previous tab |
| `Esc` | Close modal / cancel |
"""


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape,q,question_mark", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Container(
            Markdown(HELP_TEXT, id="help_md"),
            Button("Close  [Esc]", id="close_help", variant="primary"),
            id="help_container",
        )

    def on_button_pressed(self, e: Button.Pressed):
        if e.button.id == "close_help":
            self.dismiss()


class AddFindingScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, engagement: str, existing: dict | None = None):
        super().__init__()
        self.engagement = engagement
        self.existing   = existing or {}

    def compose(self) -> ComposeResult:
        e = self.existing
        yield Container(
            Label("Edit Finding" if e.get("id") else "Add Finding", id="modal_title"),
            Label("Title"),
            Input(value=e.get("title", ""), id="f_title",
                  placeholder="e.g. Exposed Tomcat Manager"),
            Label("Host"),
            Input(value=e.get("host", ""), id="f_host",
                  placeholder="e.g. target.example.gov"),
            Label("Severity"),
            Select(
                [(s, s) for s in
                 ["Critical", "High", "Medium", "Low", "Informational"]],
                value=e.get("severity", "Medium"),
                id="f_severity",
            ),
            Label("Description"),
            TextArea(text=e.get("description", ""), id="f_desc"),
            Label("Evidence"),
            TextArea(text=e.get("evidence", ""), id="f_evidence"),
            Label("Impact"),
            TextArea(text=e.get("impact", ""), id="f_impact"),
            Label("Recommendation"),
            TextArea(text=e.get("recommendation", ""), id="f_rec"),
            Horizontal(
                Button("Save",   id="save_finding",   variant="success"),
                Button("Cancel", id="cancel_finding", variant="default"),
            ),
            id="finding_modal",
        )

    def on_button_pressed(self, e: Button.Pressed):
        if e.button.id == "save_finding":
            data = {
                "title":          self.query_one("#f_title",    Input).value.strip(),
                "host":           self.query_one("#f_host",     Input).value.strip(),
                "severity":       self.query_one("#f_severity", Select).value,
                "description":    self.query_one("#f_desc",     TextArea).text.strip(),
                "evidence":       self.query_one("#f_evidence", TextArea).text.strip(),
                "impact":         self.query_one("#f_impact",   TextArea).text.strip(),
                "recommendation": self.query_one("#f_rec",      TextArea).text.strip(),
            }
            if not data["title"] or not data["host"]:
                return
            if self.existing.get("id"):
                data["id"] = self.existing["id"]
            self.dismiss(data)
        else:
            self.dismiss(None)


class AddNoteScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, engagement: str):
        super().__init__()
        self.engagement = engagement

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Add Note", id="modal_title"),
            Label("Host (optional)"),
            Input(id="n_host", placeholder="e.g. target.example.gov"),
            Label("Note"),
            TextArea(id="n_content"),
            Horizontal(
                Button("Save",   id="save_note",   variant="success"),
                Button("Cancel", id="cancel_note", variant="default"),
            ),
            id="note_modal",
        )

    def on_button_pressed(self, e: Button.Pressed):
        if e.button.id == "save_note":
            host    = self.query_one("#n_host",    Input).value.strip()
            content = self.query_one("#n_content", TextArea).text.strip()
            if not content:
                return
            self.dismiss({"host": host, "content": content})
        else:
            self.dismiss(None)


class NewEngagementScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("New Engagement", id="modal_title"),
            Label("Name"),
            Input(id="eng_name",  placeholder="e.g. uscourts-vdp-2026"),
            Label("Scope (optional, one entry per line)"),
            TextArea(id="eng_scope"),
            Horizontal(
                Button("Create", id="create_eng", variant="success"),
                Button("Cancel", id="cancel_eng", variant="default"),
            ),
            id="eng_modal",
        )

    def on_button_pressed(self, e: Button.Pressed):
        if e.button.id == "create_eng":
            name  = self.query_one("#eng_name",  Input).value.strip()
            scope = self.query_one("#eng_scope", TextArea).text.strip()
            if not name:
                return
            self.dismiss({"name": name, "scope": scope})
        else:
            self.dismiss(None)


class ExportTriageScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    COLUMNS = [
        ("priority", "Priority"),
        ("status",   "Status"),
        ("host",     "Host"),
        ("title",    "Title"),
        ("tech",     "Tech"),
        ("tags",     "Tags"),
        ("ip",       "IP"),
    ]

    def __init__(self, tier: str = "all"):
        super().__init__()
        self.tier = tier

    def compose(self) -> ComposeResult:
        tier_label = self.tier.upper() if self.tier != "all" else "All"
        yield Container(
            Label(f"Export Triage — {tier_label}", id="modal_title"),
            Label("Format"),
            Select(
                [("Markdown table (.md)", "md"), ("CSV (.csv)", "csv"), ("Host list (.txt)", "txt")],
                value="md",
                id="ex_format",
            ),
            Label("Columns to include"),
            Vertical(
                *[
                    Checkbox(label, value=(key != "tags"), id=f"col_{key}")
                    for key, label in self.COLUMNS
                ],
                id="col_checkboxes",
            ),
            Horizontal(
                Button("Export", id="do_export", variant="success"),
                Button("Cancel", id="cancel_export", variant="default"),
            ),
            id="export_modal",
        )

    def on_button_pressed(self, e: Button.Pressed):
        if e.button.id == "do_export":
            fmt  = self.query_one("#ex_format", Select).value
            cols = [
                key for key, _ in self.COLUMNS
                if self.query_one(f"#col_{key}", Checkbox).value
            ]
            if not cols:
                return
            self.dismiss({"format": fmt, "columns": cols, "tier": self.tier})
        else:
            self.dismiss(None)
