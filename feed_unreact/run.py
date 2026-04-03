#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path

CLI = (Path(__file__).resolve().parent.parent / "bin" / "linkedin-cli").resolve()

KNOWN_PARAMS = {"post_urn", "reaction_type"}


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
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"output": result.stdout.decode().strip()}


def main() -> None:
    """Remove a reaction from a LinkedIn post."""
    params = json.load(sys.stdin)
    unknown = set(params) - KNOWN_PARAMS
    if unknown:
        print(f"Unknown parameters: {', '.join(sorted(unknown))}", file=sys.stderr)
        sys.exit(1)

    post_urn = params.get("post_urn")
    if not post_urn or not isinstance(post_urn, str):
        print("Missing or invalid 'post_urn' parameter.", file=sys.stderr)
        sys.exit(1)

    reaction_type = params.get("reaction_type", "LIKE")

    json.dump(
        run_cli(["feed", "unreact", post_urn, "--type", reaction_type]), sys.stdout
    )


main()
