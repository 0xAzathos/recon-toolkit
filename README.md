# recon-toolkit

A personal TUI-based recon toolkit for authorized VDP and bug bounty engagements.
Built with [Textual](https://textual.textualize.io/) and [Rich](https://rich.readthedocs.io/).

> **For authorized use only.** Only use this tool against systems you have explicit written permission to test.

---

## Features

| Module | Description |
|--------|-------------|
| Engagements | Isolate all data per program. Switch between engagements in the sidebar. |
| Triage | Paste httpx output, classify subdomains into P1-P4 priority tiers, filter and export. |
| Findings | Structured vulnerability log with severity, evidence, impact, and recommendation fields. Export to markdown. |
| Headers | Paste raw HTTP response headers for security posture scoring. Detects missing headers, cookie issues, CSP misconfigs, version disclosure. |
| Notes | Freeform timestamped notes scoped per engagement, optionally tagged to a host. |
| Scope | Define in-scope domains and IP ranges. Inline host checker to verify scope before probing. |

---

## Requirements

- Python 3.10+
- pip

---

## Installation

### Quick install (recommended)

```bash
git clone https://github.com/youruser/recon-toolkit.git
cd recon-toolkit
./install.sh
```

After install, run from anywhere:

```bash
recon
```

### Manual install

```bash
git clone https://github.com/youruser/recon-toolkit.git
cd recon-toolkit
pip install -e . --break-system-packages
```

---

## Usage

### Launch TUI

```bash
recon
```

### Launch with engagement preselected

```bash
recon --engagement uscourts-vdp-2026
```

### CLI commands (no TUI)

```bash
recon --list-engagements
recon --export-findings uscourts-vdp-2026
recon --version
```

---

## TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `?` | Open help screen |
| `q` | Quit |
| `Tab` | Next tab |
| `Shift+Tab` | Previous tab |
| `Esc` | Close modal |

---

## Data Storage

All engagement data is stored in a local SQLite database at:

```
~/.recon_toolkit.db
```

Nothing leaves your machine.

---

## Updating

```bash
cd recon-toolkit
git pull
pip install -e . --break-system-packages
```

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).
See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

MIT License. See [LICENSE](LICENSE).
