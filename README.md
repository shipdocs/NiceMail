# NiceMail

NiceMail is a Linux-first email client that wraps powerful features inside a calm, beautiful interface that seniors can enjoy. The project combines a simplified inbox experience with optional advanced controls, modern protocol support, and ChatGPT-driven spam protection.

## Highlights

- **Gentle inbox overview** – the start page focuses on the inbox with large typography and meaningful summaries.
- **Hidden complexity** – secondary folders stay out of sight until the user opts in via a friendly hint.
- **AI-powered spam management** – integrate with ChatGPT (or other OpenAI-compatible models) to detect junk quietly in the background.
- **Modern protocol support** – IMAP today, pluggable architecture to add POP3/SMTP later.
- **Offline friendly** – bundled sample data means you can preview the interface without connecting an account.

## Getting started

### Requirements

- Python 3.11+
- Qt dependencies for PySide6 (on Ubuntu/Debian: `sudo apt install python3-pyside6.qt6`)

### Installation (development)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
nicemail
```

The sample messages will be shown automatically until at least one account is configured.

### Configuration

Create `~/.config/nicemail.toml` with one or more accounts:

```toml
[[accounts]]
name = "Personal"
address = "grandma@example.com"
incoming_server = "imap.example.com"
username = "grandma@example.com"
password = "your-app-password"
protocol = "imap"
port = 993
use_ssl = true

[spam]
provider = "chatgpt"
api_key = "sk-..."
model = "gpt-4o-mini"
threshold = 0.6
```

Spam filtering is optional—leave the `api_key` empty to disable.

### Building distributables

Produce a Python wheel/sdist (install the [build](https://pypi.org/project/build/) module first with `pip install build`):

```bash
python -m build
```

Create a `.deb` package using `fpm` (recommended for simplicity):

```bash
./package/build_deb.sh 0.1.0
```

The script wraps the wheel into a Debian package, generating `nicemail_<version>_all.deb` in the `dist/` folder. You can also adapt the script to call `dpkg-deb` directly if you prefer native tooling.

## Packaging script

The `package/build_deb.sh` helper does the following:

1. Builds the wheel.
2. Extracts metadata from the project.
3. Uses `fpm` (or emits a helpful message if missing) to craft the `.deb` package with desktop entry, icon, and launcher stub.

You can redistribute the resulting package through PPAs, Flatpak, or other channels by converting from the wheel.

## Roadmap

- Add OAuth2 support for Gmail/Outlook.
- Expand protocol support (POP3/SMTP) and background sync scheduling.
- Embed a full message viewer with attachments and accessibility tooling.
- Localize the interface for more languages.

Contributions and ideas are welcome! Open an issue describing your use case or enhancement.
