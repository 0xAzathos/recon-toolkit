"""Database layer for recon-toolkit. All data stored locally in SQLite."""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".recon_toolkit.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS engagements (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            scope      TEXT DEFAULT '',
            notes      TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS findings (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement     TEXT NOT NULL,
            title          TEXT NOT NULL,
            host           TEXT NOT NULL,
            severity       TEXT NOT NULL DEFAULT 'Medium',
            description    TEXT DEFAULT '',
            evidence       TEXT DEFAULT '',
            impact         TEXT DEFAULT '',
            recommendation TEXT DEFAULT '',
            status         TEXT DEFAULT 'Open',
            created_at     TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement TEXT NOT NULL,
            host       TEXT DEFAULT '',
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS triage_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement TEXT NOT NULL,
            host       TEXT NOT NULL,
            status     INTEGER DEFAULT 0,
            title      TEXT DEFAULT '',
            tech       TEXT DEFAULT '',
            ip         TEXT DEFAULT '',
            tags       TEXT DEFAULT '',
            priority   TEXT DEFAULT 'p4',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ─── Engagements ───────────────────────────────────────────────────────────────

def list_engagements() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM engagements ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_engagement(name: str, scope: str = "") -> bool:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO engagements (name, scope) VALUES (?, ?)", (name, scope)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_engagement_scope(name: str) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT scope FROM engagements WHERE name=?", (name,)
    ).fetchone()
    conn.close()
    return row["scope"] if row else ""


def save_engagement_scope(name: str, scope: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE engagements SET scope=? WHERE name=?", (scope, name)
    )
    conn.commit()
    conn.close()


# ─── Findings ──────────────────────────────────────────────────────────────────

def list_findings(engagement: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM findings WHERE engagement=? ORDER BY created_at DESC",
        (engagement,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_finding(engagement: str, data: dict) -> None:
    conn = get_db()
    conn.execute(
        """INSERT INTO findings
           (engagement, title, host, severity, description,
            evidence, impact, recommendation)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            engagement,
            data.get("title", ""),
            data.get("host", ""),
            data.get("severity", "Medium"),
            data.get("description", ""),
            data.get("evidence", ""),
            data.get("impact", ""),
            data.get("recommendation", ""),
        ),
    )
    conn.commit()
    conn.close()


def update_finding(fid: int, data: dict) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE findings SET title=?, host=?, severity=?, description=?,
           evidence=?, impact=?, recommendation=? WHERE id=?""",
        (
            data.get("title", ""),
            data.get("host", ""),
            data.get("severity", "Medium"),
            data.get("description", ""),
            data.get("evidence", ""),
            data.get("impact", ""),
            data.get("recommendation", ""),
            fid,
        ),
    )
    conn.commit()
    conn.close()


def delete_finding(fid: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM findings WHERE id=?", (fid,))
    conn.commit()
    conn.close()


# ─── Notes ─────────────────────────────────────────────────────────────────────

def list_notes(engagement: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notes WHERE engagement=? ORDER BY created_at DESC",
        (engagement,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_note(engagement: str, host: str, content: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (engagement, host, content) VALUES (?,?,?)",
        (engagement, host, content),
    )
    conn.commit()
    conn.close()


def delete_note(nid: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id=?", (nid,))
    conn.commit()
    conn.close()


# ─── Triage ────────────────────────────────────────────────────────────────────

def save_triage_results(engagement: str, results: list[dict]) -> None:
    conn = get_db()
    conn.execute(
        "DELETE FROM triage_results WHERE engagement=?", (engagement,)
    )
    for r in results:
        conn.execute(
            """INSERT INTO triage_results
               (engagement, host, status, title, tech, ip, tags, priority)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                engagement,
                r["host"],
                r["status"],
                r["title"],
                ", ".join(r["tech"][:3]),
                r["ip"],
                ", ".join(r["tags"]),
                r["priority"],
            ),
        )
    conn.commit()
    conn.close()


def list_triage_results(engagement: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM triage_results WHERE engagement=? ORDER BY priority, host",
        (engagement,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
