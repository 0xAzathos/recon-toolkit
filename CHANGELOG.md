# Changelog

All notable changes to recon-toolkit will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2026-05-30

### Added
- Initial release
- TUI built with Textual and Rich
- Engagement management with SQLite persistence per engagement
- Triage module: parse httpx output, classify into P1-P4 priority tiers, filter, export
- Findings module: structured log with severity, host, description, evidence, impact, recommendation, status fields; export to markdown
- Headers module: paste raw HTTP response headers, score security posture, detect missing headers, cookie flag issues, CSP report-only mode, version disclosure
- Notes module: freeform timestamped notes per engagement, host-tagged
- Scope module: define in-scope domains and IP ranges, inline host checker
- Help screen accessible via `?` key at any time
- CLI mode: `--list-engagements`, `--engagement`, `--export-findings`
- Version flag: `--version`
- One-shot install script: `install.sh`
