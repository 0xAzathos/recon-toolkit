"""HTTP response header security analysis for recon-toolkit."""

SECURITY_HEADERS = {
    "strict-transport-security":    ("HSTS",                "High"),
    "content-security-policy":      ("CSP",                 "High"),
    "x-frame-options":              ("X-Frame-Options",     "Medium"),
    "x-content-type-options":       ("X-Content-Type-Options", "Medium"),
    "referrer-policy":              ("Referrer-Policy",     "Low"),
    "permissions-policy":           ("Permissions-Policy",  "Low"),
    "x-xss-protection":             ("X-XSS-Protection",    "Low"),
    "cross-origin-opener-policy":   ("COOP",                "Low"),
    "cross-origin-embedder-policy": ("COEP",                "Low"),
}

INFO_HEADERS = [
    "server", "x-powered-by", "x-aspnet-version",
    "x-aspnetmvc-version", "x-generator", "via",
]

SEVERITY_WEIGHT = {"High": 20, "Medium": 10, "Low": 5, "Info": 0}


def parse_headers(raw: str) -> dict[str, str]:
    """Parse raw HTTP header text into a lowercase key dict."""
    parsed = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip().lower()] = v.strip()
    return parsed


def analyze_headers(raw: str) -> dict:
    """
    Analyze raw HTTP response headers.

    Returns:
        present: list of (label, value, severity) for headers that are set
        issues:  list of (severity, message) for problems found
        score:   int 0-100 security score
        parsed:  dict of all parsed headers
    """
    parsed  = parse_headers(raw)
    issues  = []
    present = []

    for hdr, (label, sev) in SECURITY_HEADERS.items():
        if hdr in parsed:
            val = parsed[hdr]
            present.append((label, val, sev))

            if hdr == "content-security-policy" and "unsafe-inline" in val:
                issues.append(("Medium", f"CSP contains unsafe-inline"))
            if hdr == "x-xss-protection" and val.strip() == "0":
                issues.append(("Info", "X-XSS-Protection explicitly disabled"))
        else:
            csp_ro = "content-security-policy-report-only"
            if hdr == "content-security-policy" and csp_ro in parsed:
                issues.append(("Medium",
                    f"CSP in report-only mode (not enforced): {parsed[csp_ro][:60]}"))
            elif hdr not in ("cross-origin-opener-policy",
                             "cross-origin-embedder-policy",
                             "permissions-policy"):
                issues.append((sev, f"Missing {label} header"))

    for hdr in INFO_HEADERS:
        if hdr in parsed:
            issues.append(("Info",
                f"Server info disclosed via {hdr}: {parsed[hdr]}"))

    cookies = [v for k, v in parsed.items() if k == "set-cookie"]
    for ck in cookies:
        name = ck.split("=")[0].strip()
        cl   = ck.lower()
        if "httponly" not in cl:
            issues.append(("Medium", f"Cookie missing HttpOnly: {name}"))
        if "secure" not in cl:
            issues.append(("Medium", f"Cookie missing Secure flag: {name}"))
        if "samesite" not in cl:
            issues.append(("Low", f"Cookie missing SameSite attribute: {name}"))
        elif "samesite=lax" in cl:
            issues.append(("Info", f"Cookie uses SameSite=Lax, consider Strict: {name}"))

    deduction = sum(SEVERITY_WEIGHT.get(sev, 0) for sev, _ in issues
                    if sev in ("High", "Medium", "Low"))
    score = max(0, 100 - deduction)

    return {
        "present": present,
        "issues":  issues,
        "score":   score,
        "parsed":  parsed,
    }


def score_label(score: int) -> tuple[str, str]:
    """Return (label, color) for a given score."""
    if score >= 80:
        return "Good", "green"
    if score >= 50:
        return "Fair", "yellow"
    return "Poor", "red"
