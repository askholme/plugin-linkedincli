#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS = {"keywords", "count", "start"}


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


def _compact_search_people(raw: dict) -> dict:
    results = []
    for cluster in raw.get("elements") or []:
        for item in cluster.get("items") or []:
            entity_result = (item.get("item") or {}).get("entityResult")
            if not entity_result:
                continue
            nav_url = entity_result.get("navigationUrl") or ""
            results.append(
                {
                    "name": ((entity_result.get("title") or {}).get("text") or ""),
                    "headline": (
                        (entity_result.get("primarySubtitle") or {}).get("text") or ""
                    ),
                    "location": (
                        (entity_result.get("secondarySubtitle") or {}).get("text") or ""
                    ),
                    "url": nav_url,
                    "urn": entity_result.get("entityUrn") or "",
                }
            )
    raw_paging = raw.get("paging") or {}
    paging = {
        "start": raw_paging.get("start", 0),
        "count": raw_paging.get("count", 0),
        "total": raw_paging.get("total", 0),
    }
    return {"results": results, "paging": paging}


def main() -> None:
    """Search for people on LinkedIn by keywords."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    keywords = params.get("keywords")
    if not keywords or not isinstance(keywords, str):
        print("Missing or invalid 'keywords' parameter.", file=sys.stderr)
        sys.exit(1)

    count = params.get("count", "10")
    start = params.get("start", "0")

    raw = run_cli(
        ["search", "people", keywords, "--count", str(count), "--start", str(start)]
    )
    output = _compact_search_people(raw)
    safe = json.dumps(output).replace("\\u0000", "")
    sys.stdout.write(safe)


main()
