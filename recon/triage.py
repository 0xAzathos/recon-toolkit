"""Subdomain triage logic for recon-toolkit."""

import re

P1_KW = [
    "admin", "administrator", "manager", "console", "dashboard",
    "portal", "control", "cpanel", "webmin", "plesk", "manage",
]
P2_KW = [
    "dev", "development", "staging", "stage", "test", "testing",
    "uat", "qa", "demo", "preprod", "pre-prod", "beta", "sandbox",
    "internal", "intranet", "corp", "staff", "old", "legacy",
]
FRAMEWORKS = [
    "wordpress", "drupal", "joomla", "jenkins", "gitlab", "grafana",
    "kibana", "elasticsearch", "phpmyadmin", "tomcat", "weblogic",
    "jboss", "struts",
]
AUTH_TITLES = ["login", "sign in", "authenticate", "authorization", "access", "sso", "saml"]

PRIORITY_LABELS = {
    "p1": "CRITICAL",
    "p2": "HIGH",
    "p3": "MEDIUM",
    "p4": "LOW",
}

PRIORITY_CRITERIA = {
    "p1": "Admin panels, server errors (5xx)",
    "p2": "Dev/staging/test, APIs, known frameworks",
    "p3": "Auth walls (401), forbidden (403), non-HTTP services",
    "p4": "Standard web, no notable signals",
}


def parse_httpx_line(line: str) -> dict | None:
    """Parse a single httpx output line into a structured dict."""
    line = line.strip()
    if not line:
        return None
    hm = re.match(r"^(https?://[^\s\[]+)", line)
    if not hm:
        return None
    host   = hm.group(1).rstrip("/")
    sc     = re.search(r"\[(\d{3})\]", line)
    status = int(sc.group(1)) if sc else 0
    brackets = re.findall(r"\[([^\]]+)\]", line)
    ipm  = re.search(r"\[(\d+\.\d+\.\d+\.\d+)\]", line)
    ip   = ipm.group(1) if ipm else ""
    title = next(
        (b for b in brackets
         if not re.match(r"^\d{3}$", b)
         and not re.match(r"^\d+\.\d+\.\d+\.\d+$", b)
         and len(b) > 1
         and "," not in b),
        "",
    )
    tech = [
        b for b in brackets
        if b != title
        and not re.match(r"^\d{3}$", b)
        and not re.match(r"^\d+\.\d+\.\d+\.\d+$", b)
    ]
    return {"host": host, "status": status, "title": title, "tech": tech, "ip": ip}


def classify(entry: dict) -> dict:
    """Assign priority tier and tags to a parsed httpx entry."""
    h     = entry["host"].lower()
    title = entry["title"].lower()
    tech  = " ".join(entry["tech"]).lower()
    sc    = entry["status"]
    tags  = []

    if any(k in h or k in title for k in P1_KW):
        tags.append("admin-panel")
    if any(k in tech or k in h for k in FRAMEWORKS):
        tags.append("known-framework")
    if sc == 401 or any(k in title for k in AUTH_TITLES):
        tags.append("auth-protected")
    if any(k in h for k in P2_KW):
        tags.append("dev-staging")
    if sc == 403:
        tags.append("forbidden")
    if sc >= 500:
        tags.append("server-error")
    if any(k in h for k in ["ftp", "smtp", "mail"]):
        tags.append("non-http-svc")
    if any(k in h for k in ["api", "rest", "graphql"]):
        tags.append("api-endpoint")

    if "admin-panel" in tags or sc >= 500:
        priority = "p1"
    elif "dev-staging" in tags or "known-framework" in tags or "api-endpoint" in tags:
        priority = "p2"
    elif "auth-protected" in tags or "forbidden" in tags or "non-http-svc" in tags:
        priority = "p3"
    else:
        priority = "p4"

    entry["tags"]     = tags
    entry["priority"] = priority
    return entry


def triage_lines(raw: str) -> list[dict]:
    """Parse and classify a block of httpx output. Returns list of classified entries."""
    results = []
    for line in raw.strip().splitlines():
        entry = parse_httpx_line(line)
        if entry:
            results.append(classify(entry))
    return results


def count_by_priority(results: list[dict]) -> dict:
    counts = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}
    for r in results:
        counts[r["priority"]] += 1
    return counts


def export_tier(results: list[dict], tier: str) -> str:
    """Return newline-separated hosts for a given tier (or all)."""
    filtered = results if tier == "all" else [r for r in results if r["priority"] == tier]
    if tier == "all":
        lines = [
            f"{r['priority'].upper()}\t[{r['status']}]\t{r['host']}\t"
            f"{', '.join(r['tags'])}\t{r['title']}"
            for r in filtered
        ]
    else:
        lines = [r["host"] for r in filtered]
    return "\n".join(lines)
