#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS: set[str] = set()

_VIEWERS_CARD_KEY = "com.linkedin.voyager.identity.me.wvmpOverview.WvmpViewersCard"
_SUMMARY_INSIGHT_KEY = (
    "com.linkedin.voyager.identity.me.wvmpOverview.WvmpSummaryInsightCard"
)
_FULL_PROFILE_VIEWER_KEY = "com.linkedin.voyager.identity.me.WvmpFullProfileViewer"
_PROFILE_VIEW_CARD_KEY = "com.linkedin.voyager.identity.me.WvmpProfileViewCard"
_PRIVATE_PROFILE_VIEWER_KEY = "com.linkedin.voyager.identity.me.PrivateProfileViewer"
_ANON_PROFILE_VIEW_CARD_KEY = (
    "com.linkedin.voyager.identity.me.WvmpAnonymousProfileViewCard"
)
_GENERIC_CARD_KEY = "com.linkedin.voyager.identity.me.WvmpGenericCard"
_PREMIUM_UPSELL_KEY = "com.linkedin.voyager.identity.me.WvmpPremiumUpsellCard"


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


def _parse_viewer_card(card: dict) -> dict | None:
    """Parse a single viewer card into a compact viewer dict, or None to skip."""
    value = card.get("value") or {}

    if _PROFILE_VIEW_CARD_KEY in value:
        pvc = value[_PROFILE_VIEW_CARD_KEY] or {}
        viewer_union = pvc.get("viewer") or {}
        full = viewer_union.get(_FULL_PROFILE_VIEWER_KEY) or {}
        profile = (full.get("profile") or {}).get("miniProfile") or {}
        first = profile.get("firstName") or ""
        last = profile.get("lastName") or ""
        headline = profile.get("occupation") or ""
        return {
            "type": "named",
            "name": f"{first} {last}".strip(),
            "headline": headline,
        }

    if _PRIVATE_PROFILE_VIEWER_KEY in value:
        ppv = value[_PRIVATE_PROFILE_VIEWER_KEY] or {}
        return {"type": "private", "headline": ppv.get("headline") or ""}

    if _ANON_PROFILE_VIEW_CARD_KEY in value:
        apvc = value[_ANON_PROFILE_VIEW_CARD_KEY] or {}
        return {"type": "anonymous", "count": apvc.get("numViewers") or 0}

    if _GENERIC_CARD_KEY in value:
        gc = value[_GENERIC_CARD_KEY] or {}
        headline_obj = gc.get("headline") or {}
        return {"type": "aggregated", "text": headline_obj.get("text") or ""}

    if _PREMIUM_UPSELL_KEY in value:
        return None  # skip premium upsell cards

    return None


def _compact_viewers(raw: dict) -> dict:
    view_change_pct = None
    viewers = []

    for el in raw.get("elements") or []:
        el_value = el.get("value") or {}
        viewers_card = el_value.get(_VIEWERS_CARD_KEY) or {}
        for insight_card in viewers_card.get("insightCards") or []:
            ic_value = insight_card.get("value") or {}
            summary = ic_value.get(_SUMMARY_INSIGHT_KEY) or {}
            if summary:
                if view_change_pct is None:
                    view_change_pct = summary.get("numViewsChangeInPercentage")
                for card in summary.get("cards") or []:
                    parsed = _parse_viewer_card(card)
                    if parsed is not None:
                        viewers.append(parsed)

    return {
        "view_change_pct": view_change_pct,
        "viewers": viewers,
    }


def main() -> None:
    """List people who recently viewed the authenticated user's profile."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    ensure_auth()

    raw = run_cli(["profile", "viewers"])
    output = _compact_viewers(raw)
    safe = json.dumps(output).replace("\\u0000", "")
    sys.stdout.write(safe)


main()
