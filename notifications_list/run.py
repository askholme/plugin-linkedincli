#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS = {"count", "start"}


def ensure_auth() -> None:
    """If no session exists, attempt auth login from config.json."""
    session_file = Path.home() / ".config" / "linkedin-cli" / "session.json"
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
        [str(CLI), "auth", "login", "--li-at", li_at], capture_output=True
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)


def run_cli(args: list[str]) -> dict:
    """Run linkedin-cli with the given args + --json, return parsed JSON."""
    result = subprocess.run(
        [str(CLI)] + args + ["--json"],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        if result.stdout:
            sys.stderr.buffer.write(result.stdout)
        sys.exit(result.returncode)
    stdout = result.stdout.replace(b"\x00", b"").replace(b"\\u0000", b"")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"output": stdout.decode().strip()}


def _compact_notifications(raw: dict) -> dict:
    notifications = []
    for el in raw.get("elements") or []:
        notifications.append(
            {
                "headline": ((el.get("headline") or {}).get("text") or ""),
                "sub_headline": ((el.get("subHeadline") or {}).get("text") or ""),
                "time": ((el.get("kicker") or {}).get("text") or ""),
                "type": el.get("contentType") or "",
                "published_at": el.get("publishedAt"),
                "read": bool(el.get("read")),
            }
        )
    raw_paging = raw.get("paging") or {}
    paging = {
        "start": raw_paging.get("start", 0),
        "count": raw_paging.get("count", 0),
        "total": raw_paging.get("total", 0),
    }
    return {"notifications": notifications, "paging": paging}


def main() -> None:
    """List LinkedIn notifications."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    count = params.get("count", "10")
    start = params.get("start", "0")

    raw = run_cli(
        ["notifications", "list", "--count", str(count), "--start", str(start)]
    )
    output = _compact_notifications(raw)
    safe = json.dumps(output).replace("\\u0000", "")
    sys.stdout.write(safe)


main()
