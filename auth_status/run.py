#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS: set[str] = set()


def ensure_auth() -> None:
    """If no session exists, attempt auth login from config.json."""
    session_dir = Path.home() / ".config" / "linkedin-cli"
    session_file = session_dir / "session.json"
    if session_file.exists():
        return
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    if not config_path.exists():
        print(
            "Not authenticated and config.json not found. Configure the plugin with a li_at cookie.",
            file=sys.stderr,
        )
        sys.exit(1)
    config = json.loads(config_path.read_text())
    li_at = config.get("li_at")
    if not li_at:
        print("Not authenticated and li_at is missing in config.json.", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run(
        [str(CLI), "auth", "login", "--li-at", li_at],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)


def main() -> None:
    """Check the current LinkedIn authentication status."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    # auth status does not support --json; capture plain text output
    result = subprocess.run(
        [str(CLI), "auth", "status"],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        if result.stdout:
            sys.stderr.buffer.write(result.stdout)
        sys.exit(result.returncode)

    json.dump({"output": result.stdout.decode().strip()}, sys.stdout)


main()
