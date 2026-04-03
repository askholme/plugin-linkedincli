#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, re, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS = {"count", "start"}

_UPDATE_V2_KEY = "com.linkedin.voyager.feed.render.UpdateV2"
_ACTIVITY_RE = re.compile(r"(urn:li:activity:[^,)]+)")


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


def _extract_activity_urn(entity_urn: str) -> str:
    """Extract urn:li:activity:... from a feed update entityUrn."""
    m = _ACTIVITY_RE.search(entity_urn or "")
    return m.group(1) if m else (entity_urn or "")


def _compact_feed(raw: dict) -> dict:
    elements = []
    for el in raw.get("elements") or []:
        entity_urn = el.get("entityUrn") or ""
        activity_urn = _extract_activity_urn(entity_urn)
        v2 = (el.get("value") or {}).get(_UPDATE_V2_KEY) or {}
        actor = v2.get("actor") or {}
        author = (actor.get("name") or {}).get("text") or ""
        commentary = v2.get("commentary") or {}
        text = ((commentary.get("text") or {}).get("text") or "") if commentary else ""
        social = v2.get("socialDetail") or {}
        counts = social.get("totalSocialActivityCounts") or {}
        likes = counts.get("numLikes") or 0
        comments = counts.get("numComments") or 0
        url = (
            f"https://www.linkedin.com/feed/update/{activity_urn}"
            if activity_urn
            else ""
        )
        elements.append(
            {
                "urn": activity_urn,
                "author": author,
                "text": text,
                "url": url,
                "likes": likes,
                "comments": comments,
            }
        )
    raw_paging = raw.get("paging") or {}
    paging = {
        "start": raw_paging.get("start", 0),
        "count": raw_paging.get("count", 0),
        "total": raw_paging.get("total", 0),
    }
    return {"elements": elements, "paging": paging}


def main() -> None:
    """List posts from the LinkedIn feed."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    count = params.get("count", "10")
    start = params.get("start", "0")

    raw = run_cli(["feed", "list", "--count", str(count), "--start", str(start)])
    output = _compact_feed(raw)
    safe = json.dumps(output).replace("\\u0000", "")
    sys.stdout.write(safe)


main()
