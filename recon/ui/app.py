"""Main TUI application for recon-toolkit."""

import re
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button, DataTable, Footer, Header, Input, Label,
    ListItem, ListView, Select, Static, TextArea, TabbedContent, TabPane
)
from rich.text import Text as TxText

from recon import __version__
from recon import db
from recon.triage import triage_lines, count_by_priority
from recon.headers import analyze_headers, score_label
from recon.export import export_findings_md, export_triage_txt
from recon.ui.screens import (
    HelpScreen, AddFindingScreen, AddNoteScreen, NewEngagementScreen
)


class ReconApp(App):

    CSS_PATH = Path(__file__).parent / "styles.tcss"

    BINDINGS = [
        Binding("q",            "quit",      "Quit"),
        Binding("question_mark","show_help", "Help"),
    ]

    TITLE = f"recon-toolkit v{__version__}"

    def __init__(self, start_engagement: str | None = None):
        super().__init__()
        self.active_engagement = start_engagement
        self.triage_filter     = "all"
        self.triage_data: list[dict] = []

    # ─── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("ENGAGEMENTS", id="sidebar_label")
                yield ListView(id="eng_list")
                yield Button("+ New Engagement", id="new_eng", variant="primary")
            with Vertical(id="main_area"):
                with TabbedContent():
                    with TabPane("Triage",   id="tab_triage"):   yield self._triage_tab()
                    with TabPane("Findings", id="tab_findings"): yield self._findings_tab()
                    with TabPane("Headers",  id="tab_headers"):  yield self._headers_tab()
                    with TabPane("Notes",    id="tab_notes"):    yield self._notes_tab()
                    with TabPane("Scope",    id="tab_scope"):    yield self._scope_tab()
        yield Footer()

    def _triage_tab(self) -> Vertical:
        return Vertical(
            Static("Paste httpx output and press Run Triage.", classes="section_title"),
            TextArea(id="triage_input"),
            Horizontal(
                Button("Run Triage",  id="run_triage",         variant="primary"),
                Button("Clear",       id="clear_triage"),
                Button("Export P1",   id="export_p1",          classes="btn_p1"),
                Button("Export P2",   id="export_p2",          classes="btn_p2"),
                Button("Export All",  id="export_all_triage"),
                id="triage_action_row",
            ),
            Horizontal(
                Button("All", id="f_all", classes="filter_btn active_filter"),
                Button("P1",  id="f_p1",  classes="filter_btn btn_p1"),
                Button("P2",  id="f_p2",  classes="filter_btn btn_p2"),
                Button("P3",  id="f_p3",  classes="filter_btn btn_p3"),
                Button("P4",  id="f_p4",  classes="filter_btn btn_p4"),
                id="filter_row",
            ),
            ScrollableContainer(
                DataTable(id="triage_table", zebra_stripes=True),
                id="triage_output",
            ),
        )

    def _findings_tab(self) -> Vertical:
        return Vertical(
            Static("Findings Log", classes="section_title"),
            Horizontal(
                Button("+ Add Finding", id="add_finding", variant="success"),
                Button("Delete",        id="del_finding", variant="error"),
                Button("Export MD",     id="export_findings_md"),
            ),
            DataTable(id="findings_table", zebra_stripes=True),
        )

    def _headers_tab(self) -> Vertical:
        return Vertical(
            Static("Paste raw HTTP response headers to analyze.", classes="section_title"),
            TextArea(id="header_input"),
            Horizontal(
                Button("Analyze", id="analyze_headers", variant="primary"),
                Button("Clear",   id="clear_headers"),
            ),
            ScrollableContainer(
                Static(id="header_output"),
                id="header_scroll",
            ),
        )

    def _notes_tab(self) -> Vertical:
        return Vertical(
            Static("Notes", classes="section_title"),
            Horizontal(
                Button("+ Add Note", id="add_note", variant="success"),
                Button("Delete",     id="del_note", variant="error"),
            ),
            DataTable(id="notes_table", zebra_stripes=True),
        )

    def _scope_tab(self) -> Vertical:
        return Vertical(
            Static("Scope Definition", classes="section_title"),
            Label("In-scope domains and IP ranges (one per line):"),
            TextArea(id="scope_area"),
            Button("Save Scope", id="save_scope", variant="success"),
            Static("", id="scope_spacer"),
            Label("Check if a host is in scope:"),
            Horizontal(
                Input(id="scope_check_input", placeholder="e.g. sub.example.gov"),
                Button("Check", id="check_scope", variant="primary"),
            ),
            Static(id="scope_check_result"),
        )

    # ─── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        db.init_db()
        self._setup_tables()
        self._load_engagements()
        if self.active_engagement:
            self._refresh_all()

    def _setup_tables(self) -> None:
        self.query_one("#triage_table", DataTable).add_columns(
            "Priority", "Status", "Host", "Title", "Tech", "Tags", "IP"
        )
        self.query_one("#findings_table", DataTable).add_columns(
            "ID", "Severity", "Host", "Title", "Status", "Date"
        )
        self.query_one("#notes_table", DataTable).add_columns(
            "ID", "Host", "Note (preview)", "Date"
        )

    # ─── Engagement management ─────────────────────────────────────────────────

    def _load_engagements(self) -> None:
        lv = self.query_one("#eng_list", ListView)
        lv.clear()
        for eng in db.list_engagements():
            name    = eng["name"]
            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
            item    = ListItem(Label(name), id=f"eng_{safe_id}")
            if name == self.active_engagement:
                item.add_class("active_eng")
            lv.append(item)

    def on_list_view_selected(self, e: ListView.Selected) -> None:
        label = e.item.query_one(Label)
        name  = str(label.content)
        self.active_engagement = name
        self._load_engagements()
        self._refresh_all()
        self.notify(f"Engagement: {name}", severity="information")

    def _on_new_engagement(self, result) -> None:
        if result:
            if db.create_engagement(result["name"], result.get("scope", "")):
                self.active_engagement = result["name"]
                self._load_engagements()
                self._refresh_all()
                self.notify(f"Created: {result['name']}", severity="information")
            else:
                self.notify("Engagement name already exists", severity="warning")

    # ─── Refresh helpers ───────────────────────────────────────────────────────

    def _refresh_all(self) -> None:
        self._refresh_triage()
        self._refresh_findings()
        self._refresh_notes()
        self._load_scope()

    def _refresh_triage(self) -> None:
        if not self.active_engagement:
            return
        self.triage_data = db.list_triage_results(self.active_engagement)
        self._render_triage_table()

    def _render_triage_table(self) -> None:
        t = self.query_one("#triage_table", DataTable)
        t.clear()
        colors = {"p1": "red", "p2": "yellow", "p3": "green", "p4": "bright_black"}
        data   = self.triage_data
        if self.triage_filter != "all":
            data = [r for r in data if r["priority"] == self.triage_filter]
        for r in data:
            color = colors.get(r["priority"], "white")
            t.add_row(
                TxText(r["priority"].upper(), style=f"bold {color}"),
                str(r["status"]) if r["status"] else "",
                r["host"],
                (r["title"] or "")[:40],
                (r["tech"]  or "")[:30],
                (r["tags"]  or "")[:40],
                r["ip"] or "",
            )

    def _refresh_findings(self) -> None:
        if not self.active_engagement:
            return
        f = self.query_one("#findings_table", DataTable)
        f.clear()
        colors = {
            "Critical": "bold red", "High": "red", "Medium": "yellow",
            "Low": "green", "Informational": "bright_black",
        }
        for r in db.list_findings(self.active_engagement):
            f.add_row(
                str(r["id"]),
                TxText(r["severity"], style=colors.get(r["severity"], "white")),
                r["host"],
                r["title"],
                r["status"],
                r["created_at"][:10],
            )

    def _refresh_notes(self) -> None:
        if not self.active_engagement:
            return
        n = self.query_one("#notes_table", DataTable)
        n.clear()
        for r in db.list_notes(self.active_engagement):
            preview = r["content"][:60].replace("\n", " ")
            n.add_row(str(r["id"]), r["host"] or "", preview, r["created_at"][:16])

    def _load_scope(self) -> None:
        if not self.active_engagement:
            return
        scope = db.get_engagement_scope(self.active_engagement)
        self.query_one("#scope_area", TextArea).load_text(scope)

    # ─── Button dispatcher ─────────────────────────────────────────────────────

    def on_button_pressed(self, e: Button.Pressed) -> None:
        bid = e.button.id

        if bid == "new_eng":
            self.push_screen(NewEngagementScreen(), self._on_new_engagement)

        elif bid == "run_triage":     self._run_triage()
        elif bid == "clear_triage":   self._clear_triage()
        elif bid == "export_p1":      self._export_triage("p1")
        elif bid == "export_p2":      self._export_triage("p2")
        elif bid == "export_all_triage": self._export_triage("all")

        elif bid in ("f_all","f_p1","f_p2","f_p3","f_p4"):
            self.triage_filter = bid[2:] if bid != "f_all" else "all"
            for b in ("f_all","f_p1","f_p2","f_p3","f_p4"):
                btn = self.query_one(f"#{b}", Button)
                if b == bid: btn.add_class("active_filter")
                else:        btn.remove_class("active_filter")
            self._render_triage_table()

        elif bid == "add_finding":
            if not self.active_engagement:
                self.notify("Select an engagement first", severity="warning"); return
            self.push_screen(AddFindingScreen(self.active_engagement), self._on_finding_saved)
        elif bid == "del_finding":    self._delete_row("findings_table", db.delete_finding)
        elif bid == "export_findings_md": self._export_findings()

        elif bid == "analyze_headers": self._analyze_headers()
        elif bid == "clear_headers":
            self.query_one("#header_input",  TextArea).load_text("")
            self.query_one("#header_output", Static).update("")

        elif bid == "add_note":
            if not self.active_engagement:
                self.notify("Select an engagement first", severity="warning"); return
            self.push_screen(AddNoteScreen(self.active_engagement), self._on_note_saved)
        elif bid == "del_note":       self._delete_row("notes_table", db.delete_note)

        elif bid == "save_scope":     self._save_scope()
        elif bid == "check_scope":    self._check_scope()

    # ─── Triage actions ────────────────────────────────────────────────────────

    def _run_triage(self) -> None:
        if not self.active_engagement:
            self.notify("Select an engagement first", severity="warning"); return
        raw     = self.query_one("#triage_input", TextArea).text
        results = triage_lines(raw)
        if not results:
            self.notify("No valid httpx lines found", severity="warning"); return
        db.save_triage_results(self.active_engagement, results)
        self._refresh_triage()
        counts = count_by_priority(results)
        self.notify(
            f"Triaged {len(results)} hosts — "
            f"P1:{counts['p1']} P2:{counts['p2']} P3:{counts['p3']} P4:{counts['p4']}",
            severity="information",
        )

    def _clear_triage(self) -> None:
        self.query_one("#triage_input", TextArea).load_text("")
        self.query_one("#triage_table", DataTable).clear()
        self.triage_data = []

    def _export_triage(self, tier: str) -> None:
        if not self.triage_data:
            self.notify("Run triage first", severity="warning"); return
        path = export_triage_txt(self.active_engagement or "export", self.triage_data, tier)
        self.notify(f"Exported to {path}", severity="information")

    # ─── Findings actions ──────────────────────────────────────────────────────

    def _on_finding_saved(self, data) -> None:
        if data:
            if data.get("id"):
                db.update_finding(data["id"], data)
            else:
                db.add_finding(self.active_engagement, data)
            self._refresh_findings()
            self.notify("Finding saved", severity="information")

    def _export_findings(self) -> None:
        if not self.active_engagement:
            return
        findings = db.list_findings(self.active_engagement)
        if not findings:
            self.notify("No findings to export", severity="warning"); return
        path = export_findings_md(self.active_engagement, findings)
        self.notify(f"Exported to {path}", severity="information")

    # ─── Headers actions ───────────────────────────────────────────────────────

    def _analyze_headers(self) -> None:
        raw = self.query_one("#header_input", TextArea).text.strip()
        if not raw:
            self.notify("Paste headers first", severity="warning"); return
        result  = analyze_headers(raw)
        score   = result["score"]
        label, color = score_label(score)
        lines   = [f"[bold {color}]Security Score: {score}/100 — {label}[/]", ""]

        if result["present"]:
            lines.append("[bold cyan]Present Headers:[/]")
            for hdr_label, val, _ in result["present"]:
                lines.append(f"  [green]✓[/] {hdr_label}: [dim]{val[:72]}[/]")
            lines.append("")

        if result["issues"]:
            lines.append("[bold cyan]Issues:[/]")
            SEV_COLOR = {"High":"red","Medium":"yellow","Low":"bright_yellow","Info":"bright_black"}
            SEV_ICON  = {"High":"✗","Medium":"!","Low":"~","Info":"i"}
            for sev, msg in result["issues"]:
                c = SEV_COLOR.get(sev, "white")
                i = SEV_ICON.get(sev,  "·")
                lines.append(f"  [{c}]{i} [{sev}][/] {msg}")
        else:
            lines.append("[green]No issues found.[/]")

        self.query_one("#header_output", Static).update("\n".join(lines))

    # ─── Notes actions ─────────────────────────────────────────────────────────

    def _on_note_saved(self, data) -> None:
        if data:
            db.add_note(self.active_engagement, data["host"], data["content"])
            self._refresh_notes()
            self.notify("Note saved", severity="information")

    # ─── Scope actions ─────────────────────────────────────────────────────────

    def _save_scope(self) -> None:
        if not self.active_engagement:
            self.notify("Select an engagement first", severity="warning"); return
        scope = self.query_one("#scope_area", TextArea).text.strip()
        db.save_engagement_scope(self.active_engagement, scope)
        self.notify("Scope saved", severity="information")

    def _check_scope(self) -> None:
        if not self.active_engagement:
            return
        host    = self.query_one("#scope_check_input", Input).value.strip()
        scope   = db.get_engagement_scope(self.active_engagement)
        entries = [s.strip() for s in scope.splitlines() if s.strip()]
        result  = self.query_one("#scope_check_result", Static)

        if not entries:
            result.update("[yellow]No scope defined for this engagement.[/]"); return

        in_scope = any(
            (e.startswith("*") and host.endswith(e[1:]))
            or host == e
            or host.endswith("." + e)
            for e in entries
        )
        if in_scope:
            result.update(f"[green]✓ {host} is IN SCOPE[/]")
        else:
            result.update(f"[red]✗ {host} is OUT OF SCOPE[/]")

    # ─── Generic delete ────────────────────────────────────────────────────────

    def _delete_row(self, table_id: str, delete_fn) -> None:
        t = self.query_one(f"#{table_id}", DataTable)
        if t.cursor_row < 0:
            return
        row = t.get_row_at(t.cursor_row)
        delete_fn(int(str(row[0])))
        if table_id == "findings_table":
            self._refresh_findings()
        else:
            self._refresh_notes()
        self.notify("Deleted", severity="warning")

    # ─── App actions ───────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        self.exit()
