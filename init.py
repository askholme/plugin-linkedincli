#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path


def main():
    config_path = Path("config.json")
    if not config_path.exists():
        print("config.json not found.", file=sys.stderr)
        sys.exit(1)
    config = json.loads(config_path.read_text())
    li_at = config.get("li_at")
    if not li_at:
        print("li_at is missing in config.json.", file=sys.stderr)
        sys.exit(1)

    cli = (Path(__file__).resolve().parent / "bin" / "linkedin-cli").resolve()
    result = subprocess.run(
        [str(cli), "auth", "login", "--li-at", li_at],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    output = result.stdout.decode().strip()
    json.dump({"status": "ok", "message": output}, sys.stdout)


main()
