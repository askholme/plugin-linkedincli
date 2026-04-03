#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS = {"public_id"}


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


def _compact_profile(raw: dict) -> dict:
    """Extract compact profile fields from a GraphQL profile response."""
    # GraphQL response: unwrap first element if wrapped in elements[]
    if "elements" in raw:
        elements = raw.get("elements") or []
        profile = elements[0] if elements else {}
    else:
        profile = raw

    public_id = profile.get("publicIdentifier") or ""
    url = f"https://www.linkedin.com/in/{public_id}" if public_id else ""

    geo = (profile.get("geoLocation") or {}).get("geo") or {}
    location = geo.get("defaultLocalizedName") or ""

    industry_obj = profile.get("industry") or {}
    industry = industry_obj.get("name") or ""

    positions = []
    pos_groups = profile.get("profilePositionGroups") or {}
    for group in pos_groups.get("elements") or []:
        inner = group.get("profilePositionInPositionGroup") or {}
        for pos in inner.get("elements") or []:
            dr = pos.get("dateRange") or {}
            positions.append(
                {
                    "title": pos.get("title") or "",
                    "company": pos.get("companyName") or "",
                    "start_year": ((dr.get("start") or {}).get("year")),
                    "end_year": ((dr.get("end") or {}).get("year")),
                }
            )

    education = []
    edu_obj = profile.get("profileEducations") or {}
    for edu in edu_obj.get("elements") or []:
        dr = edu.get("dateRange") or {}
        education.append(
            {
                "school": edu.get("schoolName") or "",
                "degree": edu.get("degreeName") or "",
                "field": edu.get("fieldOfStudy") or "",
                "start_year": ((dr.get("start") or {}).get("year")),
                "end_year": ((dr.get("end") or {}).get("year")),
            }
        )

    return {
        "first_name": profile.get("firstName") or "",
        "last_name": profile.get("lastName") or "",
        "headline": profile.get("headline") or "",
        "summary": profile.get("summary") or "",
        "location": location,
        "industry": industry,
        "public_id": public_id,
        "urn": profile.get("entityUrn") or "",
        "url": url,
        "positions": positions,
        "education": education,
    }


def main() -> None:
    """View a LinkedIn profile by public identifier."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    public_id = params.get("public_id")
    if not public_id or not isinstance(public_id, str):
        print("Missing or invalid 'public_id' parameter.", file=sys.stderr)
        sys.exit(1)

    raw = run_cli(["profile", "view", public_id])
    output = _compact_profile(raw)
    safe = json.dumps(output).replace("\\u0000", "")
    sys.stdout.write(safe)


main()
